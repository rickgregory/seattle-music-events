#!/usr/bin/env python3
"""Generate index.html (90-day calendar) and edmonds_center_arts_season.html."""
import json, re, html, datetime, urllib.parse, collections, os

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPER_DIR = os.path.join(PROJ, 'scraper')
OUTDIR = PROJ
TODAY = datetime.date.today()
HORIZON = TODAY + datetime.timedelta(days=90)
REFRESH = TODAY.strftime('Last refreshed: %a, %b %d, %Y').replace(' 0', ' ')
STAMP = TODAY.strftime('%b %d, %Y').replace(' 0', ' ')

def esc(s):
    return html.escape(s or '', quote=True)

def slugcls(g):
    return 'g-' + re.sub(r'[^a-z0-9]+', '-', g.lower()).strip('-')

def fmt(d):
    return d.strftime('%a, %b %d, %Y')

CSS_INDEX = """:root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2330;--ink:#e6edf3;--muted:#8b949e;--accent:#f7784b;--accent2:#58a6ff;--line:#30363d;}
*{box-sizing:border-box;}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.45;}
header{padding:36px 24px 22px;text-align:center;background:linear-gradient(160deg,#1a1208,#0d1117 70%);border-bottom:1px solid var(--line);}
header h1{margin:0 0 6px;font-size:2rem;letter-spacing:.5px;}header h1 .em{color:var(--accent);}header p{margin:3px 0;color:var(--muted);font-size:.92rem;}
.pagenav{margin-top:14px;font-size:.85rem;}
.pagenav a{color:var(--accent2);text-decoration:none;border-bottom:1px dotted var(--accent2);}
.pagenav a:hover{color:var(--accent);border-bottom-color:var(--accent);}
.suggest-btn{display:inline-block;margin-left:26px;padding:5px 14px;border:1px solid var(--accent);border-radius:20px;color:var(--accent) !important;border-bottom:none !important;font-weight:600;}
.suggest-btn:hover{background:var(--accent);color:#1a0d06 !important;}
.lastref{margin-top:10px;font-size:.74rem;color:var(--muted);}
.wrap{max-width:1100px;margin:0 auto;padding:24px 16px 50px;}
.meta{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:10px;}
.meta div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 18px;} .meta b{color:var(--accent2);font-size:1.4rem;display:block;} .meta span{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:1px;}
.note{font-size:.78rem;color:var(--muted);text-align:center;margin:0 0 10px;}
.flbl{font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;text-align:center;margin:14px 0 6px;}
.filters{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-bottom:6px;}
.fbtn{background:var(--panel);color:var(--muted);border:1px solid var(--line);border-radius:20px;padding:6px 14px;font-size:.8rem;cursor:pointer;transition:.15s;}
.fbtn:hover{border-color:var(--accent2);color:var(--ink);} .fbtn.active{background:var(--accent);color:#1a0d06;border-color:var(--accent);font-weight:600;}
.count{text-align:center;font-size:.75rem;color:var(--muted);margin:8px 0 0;}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-top:8px;}
thead th{background:var(--panel2);color:var(--accent2);text-align:left;padding:12px 14px;font-size:.78rem;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--line);}
tbody td{padding:10px 14px;border-bottom:1px solid rgba(48,54,61,.5);vertical-align:top;font-size:.9rem;} tbody tr:last-child td{border-bottom:none;}
tbody tr:hover{background:rgba(88,166,255,.06);} td.date{white-space:nowrap;color:var(--accent2);font-weight:600;width:160px;}
td.loc{width:200px;color:var(--muted);} td.metro{width:110px;color:var(--muted);font-size:.82rem;}
.actlink{color:var(--ink);text-decoration:none;border-bottom:1px dotted var(--accent2);}
.actlink:hover{color:var(--accent);border-bottom-color:var(--accent);}
.gtag{font-size:.72rem;padding:2px 9px;border-radius:12px;background:rgba(88,166,255,.12);color:var(--accent2);white-space:nowrap;}
.g-unknown{background:rgba(139,148,158,.15);color:var(--muted);}
footer{text-align:center;color:var(--muted);font-size:.78rem;padding:22px;border-top:1px solid var(--line);}
@media(max-width:720px){thead{display:none;}tbody td{display:block;width:auto!important;padding:3px 14px;}tbody tr{display:block;border-bottom:1px solid var(--line);padding:9px 0;}td.date::before{content:"Date: ";color:var(--muted);font-weight:400;}td.genre::before{content:"Genre: ";color:var(--muted);}td.loc::before{content:"Venue: ";color:var(--muted);}td.metro::before{content:"Area: ";color:var(--muted);}}"""


def build_index():
    ev = json.load(open(f'{SCRAPER_DIR}/merged.json'))
    for e in ev:
        e['d'] = datetime.date.fromisoformat(e['date'])
    ev.sort(key=lambda e: (e['d'], e['title'].lower()))

    genres = sorted({e['genre'] for e in ev if e['genre'] != 'Unknown'})
    if any(e['genre'] == 'Unknown' for e in ev):
        genres.append('Unknown')
    areas = sorted({e['metro'] for e in ev if e['metro'] != 'Seattle'})
    areas = (['Seattle'] if any(e['metro'] == 'Seattle' for e in ev) else []) + areas
    venues = len({e['venue'].lower() for e in ev if e['venue']})

    rows = []
    for e in ev:
        rows.append(
            f'<tr data-genre="{esc(e["genre"])}" data-metro="{esc(e["metro"])}">'
            f'<td class="date">{fmt(e["d"])}</td>'
            f'<td class="act"><a class="actlink" href="{esc(e["url"])}" target="_blank" '
            f'rel="noopener">{esc(e["title"])}</a></td>'
            f'<td class="genre"><span class="gtag {slugcls(e["genre"])}">{esc(e["genre"])}</span></td>'
            f'<td class="loc">{esc(e["venue"])}</td>'
            f'<td class="metro">{esc(e["metro"])}</td></tr>')

    gf = ''.join(f'<button class="fbtn gf" data-filter="{esc(g)}">{esc(g)}</button>' for g in genres)
    af = ''.join(f'<button class="fbtn af" data-filter="{esc(a)}">{esc(a)}</button>' for a in areas)

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Seattle + North Sound Music \u2014 Next 90 Days</title><style>
{CSS_INDEX}
</style></head><body>
<header><h1>Seattle <span class="em">&amp; North Sound</span> Music</h1><p>Upcoming shows \u2014 next 90 days \u00b7 {fmt(TODAY)[5:]} \u2013 {fmt(HORIZON)[5:]}</p>
<p>Seattle + Shoreline \u00b7 Edmonds \u00b7 Kenmore \u00b7 Bothell area venues</p>
<nav class="pagenav"><a href="index.html">90-Day Calendar</a> \u00b7 <a href="edmonds_center_arts_season.html">Edmonds Center for the Arts \u2014 Full Season</a> \u00b7 <a class="suggest-btn" href="request-venue.html">Suggest a Venue</a></nav>
<p class="lastref">{REFRESH}</p></header>
<div class="wrap">
<div class="meta"><div><b>{len(ev)}</b><span>Shows</span></div><div><b>{venues}</b><span>Venues</span></div><div><b>{len(genres)}</b><span>Genres</span></div><div><b>90</b><span>Days</span></div></div>
<p class="note">Act names link to the event page on the source site (exact detail pages where available; otherwise a source search for that act). Genre from event-name keywords or MusicBrainz; \u201cUnknown\u201d when no source lists one. Compiled {STAMP} from EverOut, Do206, Edmonds Center for the Arts &amp; UW Arts Events (Bandsintown rows carried forward from the previous refresh).</p>
<div class="flbl">Filter by Genre</div><div class="filters" id="gf"><button class="fbtn gf active" data-filter="ALL">All</button>{gf}</div>
<div class="flbl">Filter by Area</div><div class="filters" id="af"><button class="fbtn af active" data-filter="ALL">All</button>{af}</div>
<p class="count" id="count"></p>
<table><thead><tr><th>Event Date</th><th>Act</th><th>Genre</th><th>Location</th><th>Area</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table>
</div>
<footer>Generated {STAMP} \u00b7 Data as listed by source sites and subject to change \u2014 verify with the venue.</footer>
<script>
const gf=document.querySelectorAll('#gf .fbtn'), af=document.querySelectorAll('#af .fbtn');
const rows=Array.from(document.querySelectorAll('tbody tr'));
const cnt=document.getElementById('count');
let gF='ALL', aF='ALL';
function apply(){{let n=0;rows.forEach(r=>{{const ok=(gF==='ALL'||r.dataset.genre===gF)&&(aF==='ALL'||r.dataset.metro===aF);r.style.display=ok?'':'none';if(ok)n++;}});cnt.textContent=n+' of '+rows.length+' shows shown';}}
gf.forEach(b=>b.addEventListener('click',()=>{{gf.forEach(x=>x.classList.remove('active'));b.classList.add('active');gF=b.dataset.filter;apply();}}));
af.forEach(b=>b.addEventListener('click',()=>{{af.forEach(x=>x.classList.remove('active'));b.classList.add('active');aF=b.dataset.filter;apply();}}));
apply();
</script></body></html>"""
    open(f'{OUTDIR}/index.html', 'w', encoding='utf-8').write(doc)
    return len(ev), genres, areas, venues


CSS_ECA = CSS_INDEX.replace('max-width:1100px', 'max-width:900px')


def build_eca():
    ev = json.load(open(f'{SCRAPER_DIR}/eca_all.json'))
    seen, uniq = set(), []
    for e in ev:
        k = (e['title'].lower().strip(), e['date'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)
    for e in uniq:
        e['d'] = datetime.date.fromisoformat(e['date'])
    uniq = [e for e in uniq if e['d'] >= TODAY]
    uniq.sort(key=lambda e: (e['d'], e['title'].lower()))

    def kind(t):
        tl = t.lower()
        if re.search(r'gala|auction|tour|workshop|class|fundrais', tl):
            return 'Other'
        if re.search(r'comedy|stand[- ]?up|improv|hyprov|lovitz|solo by|theatre|theater|'
                     r'ballet|swan lake|magic', tl):
            return 'Music/Theatre'
        return 'Music'

    rows = []
    for e in uniq:
        k = kind(e['title'])
        rows.append(
            f'<tr data-kind="{esc(k)}"><td class="date">{fmt(e["d"])}</td>'
            f'<td class="act"><a class="actlink" href="{esc(e["url"])}" target="_blank" '
            f'rel="noopener">{esc(e["title"])}</a></td>'
            f'<td class="time">{esc(e.get("time") or "")}</td>'
            f'<td class="kind">{esc(k)}</td></tr>')
    kinds = sorted({kind(e['title']) for e in uniq})
    kf = ''.join(f'<button class="fbtn" data-filter="{esc(k)}">{esc(k)}</button>' for k in kinds)
    span = f'{uniq[0]["date"]} \u2192 {uniq[-1]["date"]}' if uniq else 'n/a'

    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Edmonds Center for the Arts \u2014 Full Season</title><style>
{CSS_ECA}
td.time{{width:90px;color:var(--muted);}}
@media(max-width:640px){{td.time::before{{content:"Time: ";color:var(--muted);}}td.kind::before{{content:"Type: ";color:var(--muted);}}}}
</style></head><body>
<header><h1>Edmonds Center for the Arts <span class="em">\u2014 Full Season</span></h1><p>All listed upcoming events \u00b7 compiled {STAMP}</p>
<p>Source: edmondscenterforthearts.org/events</p>
<nav class="pagenav"><a href="edmonds_center_arts_season.html">ECA Full Season</a> \u00b7 <a href="index.html">90-Day Calendar</a> \u00b7 <a class="suggest-btn" href="request-venue.html">Suggest a Venue</a></nav>
<p class="lastref">{REFRESH}</p></header>
<div class="wrap">
<div class="meta"><div><b>{len(uniq)}</b><span>Shows</span></div><div><b>{span}</b><span>Date Span</span></div></div>
<p class="note">"Type" is a rough auto-tag (Music / Music-Theatre / Other) and may misclassify \u2014 verify with the venue. Times shown in venue's listed format. Event titles link to the ECA detail page.</p>
<div class="filters"><button class="fbtn active" data-filter="All">All</button>{kf}</div>
<table><thead><tr><th>Event Date</th><th>Act / Event</th><th>Time</th><th>Type</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table>
</div>
<footer>Generated {STAMP} \u00b7 Data as listed by the venue and subject to change \u2014 verify at edmondscenterforthearts.org</footer>
<script>
const btns=document.querySelectorAll('.fbtn');const rows=document.querySelectorAll('tbody tr');
btns.forEach(b=>b.addEventListener('click',()=>{{btns.forEach(x=>x.classList.remove('active'));b.classList.add('active');
const f=b.dataset.filter;rows.forEach(r=>{{r.style.display=(f==='All'||r.dataset.kind===f)?'':'none';}});}}));
</script></body></html>"""
    open(f'{OUTDIR}/edmonds_center_arts_season.html', 'w', encoding='utf-8').write(doc)
    return len(uniq)


if __name__ == '__main__':
    n, genres, areas, venues = build_index()
    m = build_eca()
    print(f'index.html: {n} shows, {venues} venues, {len(genres)} genres, {len(areas)} areas')
    print(f'genres: {genres}')
    print(f'areas: {areas}')
    print(f'edmonds_center_arts_season.html: {m} shows')
    print(f'refresh line: {REFRESH}')
