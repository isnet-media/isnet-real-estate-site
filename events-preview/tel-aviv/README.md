# TLVNET event intake

The TLVNET public guide reads `events-preview/tel-aviv/data/events.json` through its validated `/api/public-events` endpoint. No admin credentials or AI API calls are needed for this factual collector.

Run `python scripts/collect_tlvnet_events.py`. The existing `tlvnet-events.yml` workflow runs twice a day, with a single concurrency group; do not create a parallel collector. It also runs on changes to the collector or culture source inventory.

## Culture inventory (publisher / Alda, 2026-11-08)

`culture-sources.json` contains all 20 requested theatres and 18 requested concert/live music venues. It is an input to the collector: known adapters are selected from its `collector` values. `culture-coverage.json` is regenerated on each run and distinguishes active adapters, failed adapters and targets awaiting an adapter. A requested venue or discovery link is **not** evidence that collection works.

Initial connected requested venues: Beit Lessin, Cameri, Gesher, Lowy Hall, Zucker Hall, Studio Annette/Felicja Blumental, Levontin 7. The broader feed also includes Beit Ariela. The other 31 requested venues remain a development backlog; do not claim complete coverage or demand statistics. The publisher's existing maintenance agent is responsible for expanding these adapters incrementally with verified first-run output.

## Acceptance rules

- Use the primary official calendar. Every occurrence needs a full title, explicit date and performance time, actual Tel Aviv venue, HTTPS source URL and verification time.
- `theatre` is for plays and musicals. Cameri's courses and generic hosted meetings are not classified as theatre. Gesher's own Jaffa halls are accepted; touring venues are excluded.
- Concerts use `category: music` plus `concert_kind: classical | live`. Classical/chamber requires explicit program cues; the broader live music filter does not imply that a performance is non-classical. A hall alone does not establish genre: talks, book launches, comedy and dance are excluded.
- No guessed recurring dates, prices, availability, popularity or image rights. No copied marketing descriptions. Preserve actual verification times and images already covered by documented publicity permission.
- Dedupe by title, exact start and venue as well as stable record IDs. Failed sources retain only future records verified within 48 hours. The public UI also hides stale and past records.
- `production_url` can supplement an exact dated booking URL; it does not replace occurrence evidence. Image collection is independent and must keep its rights checks.
- Before publishing an adapter, test a real future occurrence and confirm API and guide read-back. Keep human edits and other city feeds intact.
