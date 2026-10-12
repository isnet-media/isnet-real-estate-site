# Ashdod local source rebuild

The publisher authorized replacement of all old Ashdod **local-source** cards on
12 October 2026. National-board, Mevalim, sports and cinema records are outside
this reset. The initial local records are retained in the recoverable Git-backed
`events-preview/admin/data/ashdod-local-reset-backup.json`.

`scripts/sync_ashdod_local.py` owns the local source intake. The legacy collector
no longer collects the three local sources it previously owned.

| Source | Reading contract |
| --- | --- |
| Ashdod Smarticket | All dated future listing occurrences; open individual card; structured date, clock, location, price, source description and image. Covers municipal community centres, library, museums, Monart and local programmes advertised there. |
| Mishkan Smarticket | Same contract, with deduplication against national-board performances. |
| Ofek | Public dated category listings and individual civil date/hour confirmation; seniors activity classification; never infer new recurrence dates from a course brochure. Missing meeting point is explicit. |
| UP60 Coing | Read the public community id and advertised public paginated listing endpoint; open individual cards. Undated services/interested-registration cards go to the scan report, never get invented dates. |
| Ironit | Homepage and advertised calendar event links; explicit event schema or source-exported Outlook calendar facts; source booking link, description and event-image provenance. Unsupported calendar structure goes to the report. |
| Municipal cultural department | Follow its advertised events calendar and cards. Report denied reads; never claim complete coverage after a failed read. |

Local source descriptions are preserved when present; a missing description
gets only a factual title/location/date/hour line. No editorial length test,
AI rewrite, workshop exclusion or taxonomy gate blocks a dated event. Missing
categories are noted for mapping. This does not infer a target audience,
programme, speaker, price or address absent from the source.

Image checks verify the response is an image. Repeated generic imagery, logos,
site-root URLs, placeholders and explicit Unsplash imagery are not automatically
published as event photos. Appropriate existing topical photo-bank illustrations
are used when available and labelled as illustrations. A source-card image's
provenance is not a claim that its scene was independently identified.

The daily workflow is scheduled at 06:20 UTC, after the national-board scan.
It reads outside the write lock merge, then resets to the latest main and merges
its snapshot before pushing. Rebuilt good cards survive a later source failure;
legacy distorted text and generic images do not. Cancellation is copied when
explicitly indicated in structured event status. Disappearance alone is not
treated as a verified cancellation. Scan results and undated services are public
admin reports; internal event notes are not event descriptions.
