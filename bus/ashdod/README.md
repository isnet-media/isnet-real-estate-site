# מתי יש אוטובוס? — Ashdod pilot

Public route: https://isnet.co.il/bus/ashdod/

An Ashdod-first, buildless, Hebrew mobile transit planner using an extracted official Israeli GTFS bus network. It supports origin stops in Ashdod and destination stops in the city or other cities/areas served by the extracted network. A city target means the last served stop in that city on each proposed itinerary, explicitly identified; it is not a street-address destination or a promise of national network completeness.

## Implemented

- Search physical bus stops by name/city/code and common Ashdod destination aliases.
- Separate intracity/intercity tabs and destination shortcuts.
- Exact GTFS calendars, date/time selection in Israel time, service beyond midnight, pickup/dropoff restrictions.
- Direct bus trips and up to one same-physical-stop transfer with a two minute scheduled minimum. No invented walking transfers.
- Planned boarding/alighting times, journey duration, wait from query time, stop list and next departures in the same direction. Frequency uses the actual gaps between displayed departures, not `60 / number of trips`.
- Group identical source stop aliases by stop code and coordinates.
- Permission-based browser geolocation. Nearby Ashdod stops use explicitly labelled straight-line distance; external walking directions are user-initiated. Coordinates are not stored or sent to our server, and are not included in shared search links.
- Shareable search parameters and clear empty/error/expired-feed states.
- No live predictions, fares, payments, rail, full national transfers, street geocoder or validated pedestrian routing in this pilot. No native mobile-app claims. No generated photos needed for this task-oriented interface.

## Sources and refresh

The collector uses https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip . It scans stop times to find routes that actually serve Ashdod, then extracts the complete relevant trip stop sequences and calendars. No competitor scraping in production. Full source archive remains temporary, not in the public repository. SHA-256 provenance and extraction time are embedded in the compact JSON. HTTP failures or failed tests do not commit new data. The interface stops offering searches after the feed's validity expires.

GitHub Actions refreshes daily. The Pages workflow subscribes to the collector workflow completion so bot pushes are published too. The committed JSON is a working snapshot, not demonstration data.

## Validation

`node --check bus/ashdod/app.js`
`node --check bus/ashdod/engine.js`
`node --test scripts/test_ashdod_bus.cjs`
`python scripts/collect_ashdod_bus.py --feed /path/to/official.zip`

22 meaningful tests cover connection margins, same-stop aliases, calendars, pickup/dropoff constraints, midnight, city targets, later feeder selection, dominated itinerary removal and real Ashdod/intercity journeys. Final browser QA covers the public deployed mobile and desktop flows.


## Rail-terminal destination and search workspace repair (2026-10-30)

A known place target now groups the official bus stops in the Ashdod Ad Halom / BIG terminal within 250 m of the terminal reference point, using their source names. Grouping is destination-only: boarding/transfer stop aliases and pickup/dropoff rules are unchanged. Explicit stop searches preserve the exact stop; the old untyped destination link to stop 52242 is migrated to the rail-complex target. The reported Friday 08:53 Rogozin/Haim Moshe Shapira case is frozen as a small source-derived regression fixture and finds direct line 7 to the actual dropoff stop 52243.

On submission the results occupy the same hero workspace as the search: side by side on desktop and immediately following the form on mobile. Destination shortcuts stay below both, and editing a search retains the compact workspace.
