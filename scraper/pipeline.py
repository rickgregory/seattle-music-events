#!/usr/bin/env python3
"""Seattle music events pipeline: parse sources -> dedupe -> window -> genre -> HTML."""
import re, html, json, os, sys, urllib.request, urllib.parse, datetime, glob, unicodedata

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPER_DIR = os.path.join(PROJ, 'scraper')
SME = os.path.join(SCRAPER_DIR, 'fetched')
OUTDIR = PROJ
TODAY = datetime.date.today()
HORIZON = TODAY + datetime.timedelta(days=90)

MONTHS = {m: i for i, m in enumerate(
    ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'], 1)}

def rd(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()

def clean(s):
    s = re.sub(r'(?s)<[^>]+>', ' ', s or '')
    s = html.unescape(s)
    s = s.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', s).strip()

def parse_date_text(t):
    """Parse 'Oct. 2, 2026' / 'Sat, Oct 17, 2026' / 'Tue Aug 18' -> date."""
    if not t:
        return None
    t = clean(t)
    m = re.search(r'([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:,\s*(\d{4}))?', t)
    if not m:
        return None
    mon = MONTHS.get(m.group(1)[:3].lower())
    if not mon:
        return None
    day = int(m.group(2))
    yr = int(m.group(3)) if m.group(3) else TODAY.year
    try:
        d = datetime.date(yr, mon, day)
    except ValueError:
        return None
    # no year given and date already well past -> next year
    if not m.group(3) and (TODAY - d).days > 60:
        try:
            d = datetime.date(yr + 1, mon, day)
        except ValueError:
            return None
    return d

# ---------------------------------------------------------------- sources
def parse_everout():
    """Parses the curated /seattle/music/ page (fetched by curl in run.sh).
    Known gap: EverOut's full "Live Music" category feed
    (everout.com/seattle/events/?category=live-music) has more events (e.g.
    smaller bar/support-act shows) but sits behind an AWS WAF JS challenge
    that curl can't solve, and is paginated per-day. See README "Known
    limitations" before trying to "fix" missing EverOut events here — it's
    not a parsing bug."""
    out, h = [], rd(f'{SME}/everout.html')
    for blk in re.split(r'(?=<div class="item-card occurrence-card card">)', h)[1:]:
        blk = blk[:4000]
        m = re.search(r'<a class="item-title[^"]*"\s+href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not m:
            continue
        url, title = m.group(1), clean(m.group(2))
        dm = re.search(r'data-date="(\d{4})-(\d{2})-(\d{2})"', blk)
        if dm:
            d = datetime.date(*map(int, dm.groups()))
        else:
            sec = re.search(r'<div class="card-secondary">(.*?)</div>', blk, re.S)
            d = parse_date_text(sec.group(1) if sec else '')
        if not d or not title:
            continue
        vm = re.search(r'\bat\s+([^<\n]{2,80})', re.sub(r'(?s)<br>', '\n', clean_keep(blk)))
        venue = clean(vm.group(1)) if vm else ''
        out.append(dict(title=title, date=d, venue=venue, url=url, src='EverOut'))
    return out

def clean_keep(blk):
    sec = re.search(r'<div class="card-secondary">(.*?)</div>', blk, re.S)
    return sec.group(1) if sec else ''

def parse_do206():
    out = []
    for fp in sorted(glob.glob(f'{SME}/do206_days/*.html')):
        h = rd(fp)
        for blk in re.split(r'(?=<div class="ds-listing event-card)', h)[1:]:
            blk = blk[:6000]
            pm = re.search(r'data-permalink="(/events/(\d{4})/(\d{1,2})/(\d{1,2})/[^"]*)"', blk)
            tm = re.search(r'<span class="ds-listing-event-title-text"[^>]*>(.*?)</span>', blk, re.S)
            if not (pm and tm):
                continue
            title = clean(tm.group(1))
            d = datetime.date(int(pm.group(2)), int(pm.group(3)), int(pm.group(4)))
            vn = re.search(r'<div class="ds-venue-name".*?<span itemprop="name"[^>]*>(.*?)</span>',
                           blk, re.S)
            if not vn:
                vn = re.search(r'<div class="ds-venue-name".*?</a>\s*(?:<[^>]+>\s*)*([^<]{2,70})',
                               blk, re.S)
            venue = clean(vn.group(1)) if vn else ''
            if not title:
                continue
            out.append(dict(title=title, date=d, venue=venue,
                            url='https://do206.com' + pm.group(1), src='Do206'))
    return out

def parse_eca():
    out, h = [], rd(f'{SME}/eca.html')
    for blk in re.split(r'(?=<div class="item-details">)', h)[1:]:
        blk = blk[:2500]
        m = re.search(r'<div class="meta-title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>', blk, re.S)
        dm = re.search(r'<span class="meta-date">(.*?)</span>', blk, re.S)
        tm = re.search(r'<span class="meta-time">(.*?)</span>', blk, re.S)
        if not (m and dm):
            continue
        d = parse_date_text(dm.group(1))
        title = clean(m.group(2))
        if not (d and title):
            continue
        out.append(dict(title=title, date=d, venue='Edmonds Center for the Arts',
                        url=m.group(1), src='ECA', time=clean(tm.group(1)) if tm else ''))
    return out

def parse_uw():
    out = []
    for fp in [f'{SME}/uw0.html', f'{SME}/uw1.html']:
        if not os.path.exists(fp):
            continue
        h = rd(fp)
        for blk in re.split(r'(?=<div\s+class="card__copy">)', h)[1:]:
            blk = blk[:3000]
            dm = re.search(r'class="card__supertitle"[^>]*>(.*?)</p>', blk, re.S)
            tm = re.search(r'class="card__title"[^>]*>(.*?)</h2>', blk, re.S)
            if not (dm and tm):
                continue
            d = parse_date_text(dm.group(1))
            act = clean(tm.group(1))
            # split act name at first lowercase-sentence blurb (skill guidance)
            act = re.split(r'\s+(?=[a-z]{3,}\s)', act)[0].strip() or act
            if not (d and act):
                continue
            vm = re.search(r'class="card__link card__link--minor"[^>]*>(.*?)</a>', blk, re.S)
            venue = clean(vm.group(1)) if vm else 'UW Campus'
            if venue.lower() in ('more info', 'buy tickets', ''):
                venue = 'UW Campus'
            out.append(dict(title=act, date=d, venue=f'{venue} (UW)', src='UW Arts',
                            url='https://artsevents.washington.edu/artsuw-events?title='
                                + urllib.parse.quote(act)))
    return out

def carry_bandsintown():
    """Bandsintown blocks curl and no browser is available under cron.
    Carry forward previously-collected rows that are still in the window."""
    p = f'{OUTDIR}/index.html'
    if not os.path.exists(p):
        return []
    h, out = rd(p), []
    for tr in re.findall(r'<tr data-genre=.*?</tr>', h, re.S):
        if 'bandsintown.com' not in tr:
            continue
        dm = re.search(r'<td class="date">(.*?)</td>', tr, re.S)
        am = re.search(r'<a class="actlink" href="([^"]+)"[^>]*>(.*?)</a>', tr, re.S)
        vm = re.search(r'<td class="loc">(.*?)</td>', tr, re.S)
        if not (dm and am):
            continue
        d = parse_date_text(dm.group(1))
        if not d:
            continue
        out.append(dict(title=clean(am.group(2)), date=d,
                        venue=clean(vm.group(1)) if vm else '',
                        url=html.unescape(am.group(1)), src='Bandsintown'))
    return out

# ---------------------------------------------------------------- genre
GENRE_MAP = {
    'soul': 'Soul/Funk', 'r&b': 'Soul/Funk', 'rhythm and blues': 'Soul/Funk',
    'funk': 'Soul/Funk', 'motown': 'Soul/Funk',
    'rock': 'Rock', 'metal': 'Rock', 'punk': 'Rock', 'indie rock': 'Rock',
    'hard rock': 'Rock', 'alternative rock': 'Rock', 'heavy metal': 'Rock',
    'garage rock': 'Rock', 'post-punk': 'Rock', 'grunge': 'Rock', 'emo': 'Rock',
    'indie': 'Alternative', 'alternative': 'Alternative', 'shoegaze': 'Alternative',
    'dream pop': 'Alternative', 'post-rock': 'Alternative',
    'electronic': 'Electronic', 'techno': 'Electronic', 'house': 'Electronic',
    'edm': 'Electronic', 'trance': 'Electronic', 'dubstep': 'Electronic',
    'ambient': 'Electronic', 'idm': 'Electronic', 'synthpop': 'Electronic',
    'drum and bass': 'Electronic', 'electro': 'Electronic',
    'jazz': 'Jazz', 'bebop': 'Jazz', 'big band': 'Jazz', 'swing': 'Jazz',
    'folk': 'Folk/Blues', 'blues': 'Folk/Blues', 'bluegrass': 'Folk/Blues',
    'americana': 'Folk/Blues', 'singer-songwriter': 'Folk/Blues', 'roots': 'Folk/Blues',
    'country': 'Country', 'honky tonk': 'Country', 'alt-country': 'Country',
    'classical': 'Classical', 'orchestra': 'Classical', 'quartet': 'Classical',
    'piano': 'Classical', 'opera': 'Classical', 'baroque': 'Classical',
    'chamber music': 'Classical', 'contemporary classical': 'Classical',
    'reggae': 'Reggae', 'ska': 'Reggae', 'dub': 'Reggae', 'dancehall': 'Reggae',
    'pop': 'Pop', 'pop rock': 'Pop', 'k-pop': 'Pop', 'power pop': 'Pop',
    'hip hop': 'Hip-Hop/R&B', 'hip-hop': 'Hip-Hop/R&B', 'rap': 'Hip-Hop/R&B',
    'trap': 'Hip-Hop/R&B', 'contemporary r&b': 'Hip-Hop/R&B',
    'disco': 'Dance/Disco', 'dance': 'Dance/Disco', 'nu-disco': 'Dance/Disco',
    'latin': 'Latin', 'salsa': 'Latin', 'cumbia': 'Latin', 'reggaeton': 'Latin',
    'mariachi': 'Latin', 'bossa nova': 'Latin', 'tango': 'Latin',
    'world': 'World', 'afrobeat': 'World', 'celtic': 'World', 'flamenco': 'World',
    'gospel': 'Gospel', 'christian': 'Gospel',
    'experimental': 'Experimental', 'noise': 'Experimental', 'avant-garde': 'Experimental',
}
JUNK = re.compile(r'^(19|20)\d{2}|victim|unknown|non-music|spoken|comedy|seen live|'
                  r'american|british|canadian|english|female|male|band|group', re.I)

KEYWORDS = [
    (r'\btribute\b|\btribute to\b|celebrating the music', 'Tribute'),
    (r'\bfestival\b|\bfest\b(?!ival)', 'Festival'),
    (r'yacht rock', 'Yacht Rock'),
    (r'\bdrag\b|\bcabaret\b|burlesque|\bmusical\b|\bimprov\b|stand[- ]?up|\bcomedy\b', 'Cabaret/Theatre'),
    (r'\bsymphony\b|\borchestra\b|\bquartet\b|\bquintet\b|\bchamber\b|\bopera\b|'
     r'\bphilharmonic\b|\bballet\b|\bchorale\b|\bpiano recital\b|\bconcerto\b|\bsonata\b', 'Classical'),
    (r'\bdj\b|\btechno\b|\bhouse music\b|\brave\b|\bedm\b|\bbass\b|\bamapiano\b|'
     r'\belectronic\b|\bsynth\b|\btrance\b', 'Electronic'),
    (r'\bdisco\b|dance party|\bdance night\b|\bclub night\b', 'Dance/Disco'),
    (r'\bhip[- ]?hop\b|\brap\b|\bmc\b|\bcypher\b', 'Hip-Hop/R&B'),
    (r'\bjazz\b|\bbebop\b|\bbig band\b', 'Jazz'),
    (r'\breggae\b|\bska\b|\bdub\b|\bdancehall\b', 'Reggae'),
    (r'\bcountry\b|\bhonky\b|\bline dance\b|\bwestern\b', 'Country'),
    (r'\bfolk\b|\bbluegrass\b|\bblues\b|\bamericana\b|\bopen mic\b|singer[- ]songwriter', 'Folk/Blues'),
    (r'\bmetal\b|\bpunk\b|\bhardcore\b|\brock\b|\bgrunge\b|\bemo\b', 'Rock'),
    (r'\bsalsa\b|\bcumbia\b|\blatin\b|\breggaeton\b|\bbachata\b|\bmariachi\b', 'Latin'),
    (r'\bgospel\b|\bworship\b|\bchoir\b', 'Gospel'),
    (r'\bkaraoke\b|\bbingo\b|\btrivia\b|\bsound bath\b|\bsound healing\b|\btour\b|'
     r'\bmarket\b|\bworkshop\b|\bclass\b|\boffice hours\b', 'Other/Event'),
    (r'\bsoul\b|\bfunk\b|\bmotown\b', 'Soul/Funk'),
    (r'\bpop\b', 'Pop'),
]

MB_CACHE = os.path.join(SCRAPER_DIR, 'mb_cache.json')
try:
    mb_cache = json.load(open(MB_CACHE))
except Exception:
    mb_cache = {}

def keyword_genre(title):
    t = title.lower()
    for pat, g in KEYWORDS:
        if re.search(pat, t):
            return g
    return None

def strip_act(title):
    """Reduce an event title to a likely lead artist name for MusicBrainz."""
    t = re.split(r'\s+(?:w/|with|feat\.?|featuring|presents|,|\+|&|/|:|\u2013|\u2014|-\s)\s*',
                 title, 1)[0]
    t = re.sub(r'\s*\(.*?\)\s*', ' ', t)
    return t.strip(' -–—:,')

def mb_genre(act):
    key = act.lower()
    if key in mb_cache:
        return mb_cache[key]
    res = None
    try:
        q = urllib.parse.quote(f'artist:"{act}"')
        url = (f'https://musicbrainz.org/ws/2/artist/?query={q}&fmt=json&limit=1')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SeattleMusicEvents/1.0 (rickgregory local calendar)'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        arts = data.get('artists') or []
        if arts:
            a = arts[0]
            if int(a.get('score', 0)) >= 85:
                tags = [t['name'].lower() for t in (a.get('tags') or [])
                        if t.get('name')]
                # NEVER take tags[0] blindly: skip junk, require GENRE_MAP membership
                for tg in tags:
                    if JUNK.search(tg):
                        continue
                    if tg in GENRE_MAP:
                        res = GENRE_MAP[tg]
                        break
                if not res:
                    for tg in tags:
                        if JUNK.search(tg):
                            continue
                        for k, v in GENRE_MAP.items():
                            if k in tg:
                                res = v
                                break
                        if res:
                            break
    except Exception:
        res = None
    mb_cache[key] = res
    return res

# ---------------------------------------------------------------- metro
METRO_RULES = [
    (r'edmonds', 'Edmonds (N)'),
    (r'remlinger|carnation', 'Carnation (N)'),
    (r'marymoor|redmond', 'Redmond (E)'),
    (r'chateau ste|woodinville', 'Woodinville (E)'),
    (r'bastyr|kenmore', 'Kenmore (N)'),
    (r'suyematsu|bainbridge', 'Bainbridge (N)'),
    (r'shoreline', 'Shoreline (N)'),
    (r'bothell|anderson school', 'Bothell (N)'),
    (r'everett|angel of the winds', 'Everett (N)'),
    (r'tacoma|emerald queen|pantages', 'Tacoma (S)'),
    (r'white river|auburn', 'Auburn (S)'),
    (r'kent\b|accesso showare', 'Kent (S)'),
    (r'bellevue', 'Bellevue (E)'),
    (r'kirkland', 'Kirkland (E)'),
    (r'issaquah', 'Issaquah (E)'),
    (r'puyallup', 'Puyallup (S)'),
    (r'olympia', 'Olympia (S)'),
    (r'bremerton|port orchard', 'Kitsap (W)'),
    (r'snoqualmie', 'Snoqualmie (E)'),
    (r'renton', 'Renton (S)'),
    (r'burien|des moines', 'Burien (S)'),
]

def metro(venue):
    v = (venue or '').lower()
    for pat, area in METRO_RULES:
        if re.search(pat, v):
            return area
    return 'Seattle'

# ---------------------------------------------------------------- main
def canon(s):
    s = unicodedata.normalize('NFKD', (s or '').lower())
    return re.sub(r'[^a-z0-9]', '', s)

def main():
    sources, failures = {}, []
    for name, fn in [('EverOut', parse_everout), ('Do206', parse_do206),
                     ('ECA', parse_eca), ('UW Arts', parse_uw),
                     ('Bandsintown (carried)', carry_bandsintown)]:
        try:
            ev = fn()
            sources[name] = ev
            print(f'{name}: {len(ev)} raw', file=sys.stderr)
            if not ev:
                failures.append(f'{name} (0 events parsed)')
        except Exception as e:
            sources[name] = []
            failures.append(f'{name} ({type(e).__name__}: {e})')
            print(f'{name} FAILED: {e}', file=sys.stderr)

    eca_all = list(sources.get('ECA') or [])

    # merge + dedupe, priority order
    order = ['ECA', 'UW Arts', 'EverOut', 'Do206', 'Bandsintown (carried)']
    seen, merged = {}, []
    for name in order:
        for e in sources.get(name) or []:
            if not (TODAY <= e['date'] <= HORIZON):
                continue
            k = (canon(e['title'])[:50], e['date'].isoformat(), canon(e['venue'])[:24])
            k2 = (canon(e['title'])[:50], e['date'].isoformat())
            if k in seen or k2 in seen:
                continue
            seen[k] = seen[k2] = True
            merged.append(e)

    # drop obvious non-music noise
    NOISE = re.compile(r'\b(bingo|trivia|karaoke|office hours|art tour|history & art|'
                       r'free .*tour|book club|open house)\b', re.I)
    merged = [e for e in merged if not NOISE.search(e['title'])]

    # genre: keyword rules first
    need_mb = []
    for e in merged:
        g = keyword_genre(e['title'])
        e['genre'] = g
        e['metro'] = metro(e['venue'])
        if not g or g in ('Pop', 'Other/Event'):
            act = strip_act(e['title'])
            if 2 < len(act) < 60:
                e['_act'] = act
                need_mb.append(e)

    # MusicBrainz fallback, parallel + cached (skip entirely with NO_MB=1)
    if os.environ.get('NO_MB') != '1' and need_mb:
        from concurrent.futures import ThreadPoolExecutor
        acts = sorted({e['_act'] for e in need_mb})
        print(f'MB lookups: {len(acts)} distinct acts', file=sys.stderr)
        with ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(mb_genre, acts))
        for e in need_mb:
            mg = mb_cache.get(e['_act'].lower())
            if mg:
                e['genre'] = mg
    for e in merged:
        e.pop('_act', None)
        if not e['genre'] or e['genre'] == 'Other/Event':
            e['genre'] = e['genre'] or 'Unknown'
    json.dump(mb_cache, open(MB_CACHE, 'w'))

    merged.sort(key=lambda e: (e['date'], e['title'].lower()))
    print(f'MERGED: {len(merged)} in window {TODAY} .. {HORIZON}', file=sys.stderr)
    json.dump([dict(e, date=e['date'].isoformat()) for e in merged],
              open(f'{SCRAPER_DIR}/merged.json', 'w'), indent=1)
    json.dump([dict(e, date=e['date'].isoformat()) for e in eca_all],
              open(f'{SCRAPER_DIR}/eca_all.json', 'w'), indent=1)
    print('FAILURES: ' + (', '.join(failures) if failures else 'none'), file=sys.stderr)

if __name__ == '__main__':
    main()
