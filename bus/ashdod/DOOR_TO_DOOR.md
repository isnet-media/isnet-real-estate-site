# Door-to-door transport upgrade — integration contract

Status: **development only**. The current public planner still searches GTFS stops and scheduled trips. Do not claim that address-to-address walking routes or realtime arrivals are available.

## Verified implementation
- `door-to-door.js` provides coordinate validation, nearby stop candidates (straight-line only), validation of pedestrian routes, connection feasibility, and map bounds.
- These helpers are intentionally not wired to the public journey form until reliable address geocoding and pedestrian routing are deployed.
- `network.json` contains GTFS stop coordinates and scheduled transit data; it does **not** contain house-number geocodes, pedestrian paths, live ETAs, or walking accessibility.

## Required provider endpoints
All endpoints must be server-side, authenticated/rate-limited and configured for lawful production use.

1. `GET /api/bus/geocode?q=...&city=אשדוד` -> `{results:[{label,lat,lon,confidence,source} ]}`; return only verified address-level coordinates, disambiguate ambiguous addresses. Never turn a street-name match into a precise address.
2. `POST /api/bus/walk-route` with `{from:{lat,lon},to:{lat,lon}}` -> `{mode:"walking",verified:true,distanceMeters,durationSeconds,geometry:[{lat,lon},...],source,updatedAt}`. Must use a pedestrian routing profile, not driving, not a straight-line approximation. Reject incomplete/unknown paths.
3. Optional `GET /api/bus/realtime?stopCode=...` -> GTFS-RT or SIRI derived, with `updatedAt`, trip/route identity, scheduled and predicted times; display 'scheduled' unless a matching live prediction exists.

## Door-to-door algorithm
- Geocode both addresses, show disambiguation when needed.
- Candidate boarding and alighting stops: spatial prefilter, then request **verified walking routes** and rank by walking time, not crow-flight distance.
- For each candidate pair call existing GTFS scheduled transit planner, accounting for the time to walk to the boarding stop and a configurable boarding buffer.
- Compare complete arrival times, including destination walking leg, and support up to one transfer. For transfers between nearby stops, require another verified pedestrian route and sufficient time buffer.
- Render walking and transit geometry in a map. Clearly distinguish real pedestrian geometry from stop-to-stop schematic transit connections.
- If provider is unavailable, do not fabricate a route. Keep the existing stop-based planner and an explicit external planner fallback.

## Acceptance tests before launch
- Ashdod: 'מיכאל אנג׳לו 9' to 'אסותא', both address candidates verified and pedestrian geometry returned.
- Opposite-direction stop pairs, missed connection, insufficient walking time, and no accessible pedestrian path.
- Missing geocode, ambiguous house number, walking provider timeout, expired timetable, no GTFS service, and no realtime feed.
- Mobile keyboard selection, RTL layout, map loading, privacy and screen-reader labels.
- Report independently: recognized queries, routes found, and fully verified end-to-end journeys.

## Deployment gate
Do not merge or deploy before production-grade geocoding and walking routing are configured, tested, and their quotas/terms reviewed. No automated production writes in this branch.
