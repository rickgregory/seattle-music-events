# Seattle Music Events

A compiled, filterable listing of upcoming live-music shows in Seattle and the
north-suburban area (Shoreline, Edmonds, Kenmore, Bothell).

## Deliverables

- **`seattle_music_next90.html`** — Main calendar: ~82 shows across the next 90 days
  (Aug 15 – Nov 13, 2026). Columns: Event Date · Act · Genre · Location · Area.
  Includes genre + area filter buttons (client-side JS) and act names linked to the
  source's event page.
- **`edmonds_center_arts_season.html`** — Full-season page for Edmonds Center for the Arts
  (Aug–Dec 2026), with a Type filter.
- **`SESSION_SUMMARY_seattle_music_events.md`** — Notes on sources, method, and constraints.

## Sources

Aggregator-first, then venues:

- [EverOut](https://everout.com/seattle/music/) — backbone (~200 events)
- [Bandsintown](https://www.bandsintown.com/c/seattle-wa)
- [Do206](https://do206.com/events/music)
- [Edmonds Center for the Arts](https://www.edmondscenterforthearts.org/events/)
- [UW Arts Events](https://artsevents.washington.edu/artsuw-events)

## Method

Genre is inferred from event-name keywords and curated [MusicBrainz](https://musicbrainz.org)
artist tags; shows with no source-listed genre are marked "Unknown" rather than guessed.
Act names link to the exact event page where the source exposes one.

The full pipeline (source set, extraction, dedupe, genre enrichment, HTML generation) is
captured as the `local-events-calendar` Hermes skill.

## Regenerating

Open `seattle_music_next90.html` in any browser. The data is a static snapshot compiled
Aug 15, 2026 — re-run the collection pipeline to refresh.
