# Daily Ashdod cinema refresh

`Refresh verified Ashdod cinema` runs at 05:15 UTC every day (08:15 in Israeli summer time, 07:15 in winter) and can also be run manually. It updates `events-preview/ashdod/data/cinema.json` and `cinema-refresh-status.json`, commits only those two files, and triggers `Publish priceboard` through `workflow_run`. The publishing workflow checks out the current `main`, including the collector's bot commit. Unrelated concurrent commits are integrated with a normal rebase; conflicting cinema edits stop publication instead of overwriting another editor.

## Official sources and city boundaries

- Cinema City: anonymous public visitor instance from the website; public `CityDynamicPage`, `SyncPresentations` and `SyncFeatures` queries. The exact Hebrew location name and source venue location ID **1181** must both match Ashdod. Pagination must finish. `dateTime` is the official site's Israel wall-clock string; do not apply an additional UTC offset. Sold-out/private sessions are omitted.
- HOT Cinema: official `/theater/5` branch and its `/tickets/TheaterEvents2` listing with `theatreid=5`, with the date filter left empty to collect all announced dates. Every returned session must have `TheaterId=5`. Catalog IDs and detail headings must match. Non-film lectures, stand-up and theatrical storytelling are excluded.
- Neither source uses sessions from another city. No CAPTCHA is solved or bypassed. Network/source failures are reported.

## Preservation and editorial checks

A complete successful source snapshot replaces schedules for that venue alone. Removed films keep their metadata as an archive; expired dates are hidden on the public pages. A failed source retains its prior verified data. Empty listings, incomplete pagination, city identity mismatches, malformed sessions and a suspicious decline below 35% of an established listing are quarantined for review. Rich existing synopses, trailers and metadata are retained when a fresh source field is missing. Language variants are consolidated with session language metadata and old detail IDs retained as aliases.

New film synopsis excerpts are shortened and attributed; human-written synopses and independently checked trailer overrides live in `cinema-editorial.json`. Reviewed editorial text is preserved. Poster source URLs are candidates only: there is no automatic image download or permission inference. Publishing a poster requires an explicit recorded reuse permission; Cinema City's copyright notice prohibits copying without permission.

Trailer links are re-read from official cinema movie sources, including HOT detail pages. YouTube IDs are checked using oEmbed, which records title, publisher and embeddable player availability. Shared videos assigned to unrelated films are withheld. Independently reviewed publisher-channel overrides take priority and verify the publisher name. Embedding can still change later or be restricted by YouTube; the trailer dialog includes a direct YouTube fallback.

## Health and missing data

The public `cinema-refresh-status.json` and the workflow summary record per-source success, verified session counts, metadata/trailer errors and missing fields. A total source outage fails the workflow; a partial outage publishes the successful venue with preserved data for the failed venue and a warning. Reports remain available as Actions artifacts for 14 days.

At implementation verification: 63 films with current/future Ashdod screenings, 277 Cinema City sessions and 115 HOT sessions; all have synopsis, runtime and age classification. 60 have source-linked embeddable trailers. For **פנתר כפול**, **לב זהב**, **מים רבים**, the source assigns a shared unrelated video; movie-specific trailers were not independently verified after additional searches and producer-fund checks. These are gaps, not claims that trailers do not exist. Poster candidates exist, but reuse rights have not been established; no protected poster is copied.

## Checks

`python scripts/test_ashdod_cinema_refresh.py` exercises other-city rejection, partial-source failures, archive retention, variant/alias preservation and poster withholding. Existing pilot and event-date checks also pass. After a scheduled/manual run, confirm both the collector and the follow-up Pages deployment succeed, compare live `cinema.json` with `main`, and check category/menu navigation, film detail links and a trailer on the public Ashdod site.
