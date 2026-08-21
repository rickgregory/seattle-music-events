# Seattle Music Events

A compiled, filterable listing of upcoming live-music shows in Seattle and the
north-suburban area (Shoreline, Edmonds, Kenmore, Bothell).

## Deliverables

- **`index.html`** — Main calendar: shows across the next 90 days. Columns: Event Date ·
  Act · Genre · Location · Area. Includes genre + area filter buttons (client-side JS)
  and act names linked to the source's event page.
- **`edmonds_center_arts_season.html`** — Full-season page for Edmonds Center for the Arts,
  with a Type filter.
- **`SESSION_SUMMARY_seattle_music_events.md`** — Notes on sources, method, and constraints.

## Sources

Aggregator-first, then venues:

- [EverOut](https://everout.com/seattle/music/) — backbone (see **Known limitations** below)
- [Bandsintown](https://www.bandsintown.com/c/seattle-wa) — carried forward each run (see below)
- [Do206](https://do206.com/events/music)
- [Edmonds Center for the Arts](https://www.edmondscenterforthearts.org/events/)
- [UW Arts Events](https://artsevents.washington.edu/artsuw-events)

## Method

Genre is inferred from event-name keywords and curated [MusicBrainz](https://musicbrainz.org)
artist tags; shows with no source-listed genre are marked "Unknown" rather than guessed.
Act names link to the exact event page where the source exposes one.

## Regenerating

Run `scraper/run.sh` (`--no-fetch` to rebuild from already-fetched HTML in `scraper/fetched/`).
It fetches sources with `curl`, runs `scraper/pipeline.py` (parse → dedupe → 90-day window →
genre) and `scraper/gen_html.py` (writes `index.html` and `edmonds_center_arts_season.html`
into the repo root), then commits and pushes.

## Known limitations

- **EverOut coverage is partial.** The scraper fetches `everout.com/seattle/music/` with plain
  `curl`. That page is a curated subset, not EverOut's full listing. The complete "Live Music"
  category feed (`everout.com/seattle/events/?category=live-music`) is behind an AWS WAF
  JS challenge (`x-amzn-waf-action: challenge`) that `curl` cannot solve — confirmed by
  fetching it with a real browser, which resolves the challenge and shows additional
  smaller/bar-venue shows (e.g. single-support-act gigs) that never appear on the curated
  page. That full feed is also paginated per-day (`?page=N`), so covering it properly would
  mean ~90 challenge-gated page fetches per run — it would need a headless-browser fetch
  step (e.g. Playwright) in place of `curl` for EverOut. Deliberately not implemented for
  now — flagged here so the gap isn't mistaken for a parsing bug.
- **Bandsintown isn't fetched live.** It blocks `curl`, and no browser is available under
  cron, so `pipeline.py`'s `carry_bandsintown()` just carries forward whatever Bandsintown
  rows were already in `index.html` from the previous run, dropped once they age out of the
  90-day window. New Bandsintown shows won't appear unless added another way.
