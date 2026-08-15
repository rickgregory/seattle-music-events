# Seattle Music Events — Session Summary
_Compiled Aug 15, 2026_

## Deliverables (on ~/Desktop)
- **seattle_music_next90.html** — Main calendar. 82 shows across the next 90 days
  (Aug 15 – Nov 13, 2026). Columns: Event Date · Act · Genre · Location · Area.
  Genre + Area filter buttons (client-side JS). Act names link to the exact event
  page on the source (67/82 exact; rest link to a source search).
- **edmonds_center_arts_season.html** — Separate full-season page for Edmonds Center
  for the Arts (Aug–Dec 2026, 16 shows), with a Type filter.

## Sources used (aggregator-first, then venues)
- EverOut (everout.com/seattle/music) — backbone, ~200 events, exact `/events/<slug>/e<id>/` URLs
- Bandsintown (bandsintown.com/c/seattle-wa) — event links `/e/<id>-<artist>-at-<venue>`
- Do206 (do206.com/events/music) — permalinks `/YYYY/M/D/<slug>-tickets`
- Edmonds Center for the Arts (edmondscenterforthearts.org/events) — exact event URLs
- UW Arts Events (artsevents.washington.edu/artsuw-events, music filter) — Drupal AJAX;
  no extractable detail URLs, so acts link to a `?title=<act>` search

## Key decisions & constraints
- **Genre**: from event-name keywords first, then MusicBrainz curated artist tags.
  "Unknown" when nothing matches (NOT guessed). Wikipedia bio-text scraping was rejected
  as noisy (e.g. tagged "Paris Jackson" as "Nepo Baby").
- **Geography**: Shoreline / Edmonds / Kenmore / Bothell requested. Only Edmonds contributed
  real data (ECA). Shoreline/Kenmore/Bothell city calendars are JS-gated/404 (unscrapeable);
  Bandsintown "city" pages return the same Seattle-region shows. North-suburb venues that
  DID appear (Remlinger Farms/Carnation, Marymoor/Redmond, Chateau Ste. Michelle/Woodinville,
  Bastyr/Kenmore, Suyematsu/Bainbridge) are metro-tagged.
- **Ecosia / Bing / DuckDuckGo**: bot-blocked / returned junk — not used.
- **Act links**: exact event pages where the source exposes them (EverOut, Bandsintown,
  Do206, ECA); otherwise a source search. Browser was used to pull the real aggregator URLs.

## Environment fix (persisted)
- Chrome 151 "Allow remote debugging" popup: harness launches a separate Chrome at
  `~/.hermes/chrome-debug`. Fixed by adding
  `--enable-features=DevToolsAcceptDebuggingConnections:approval_disabled` to
  `_chrome_debug_args()` in `~/.hermes/hermes-agent/hermes_cli/browser_connect.py`.

## Reusable artifact
- Skill **`local-events-calendar`** (research/) saved with the full pipeline, source set,
  pitfalls, and verification steps. Load it for any future city music-calendar request.

## Open / deferred
- Do206 "today" shows (Aug 15) beyond the snapshot could get exact URLs by fetching Do206's
  full-date calendar (22 fallback links remain).
- UW Arts has no extractable detail URLs (modal-based) — only search links.
- 49/82 shows still "Unknown" genre (obscure local acts with no MusicBrainz tag).
