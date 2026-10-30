# Ashdod bus route cross-check sources (2026-10-30)

## Official operator — Electra Afikim
https://www.electra-afikim.co.il/ashdod-metrobus/

The page provides a route map per neighborhood (18 neighborhood entries) and maps for lines 1, 2/2א, 3/3א, 4א, 5, 6, 7/7א, 8/8א, 9/9א, 10, 11, 12, 20, 21, 22, 23, 26, 33 and 34. These are *reference maps*, not a substitute for the current GTFS feed.

Example PDF for line 4/4א:
https://www.electra-afikim.co.il/wp-content/themes/afikim/maps/kavim/4KavAshdod.pdf

The PDF contains an OpenStreetMap copyright date of 2022. **Do not infer that its routing, stops, or frequency are current.**

## Municipality
https://www.ashdod.muni.il/he-il/אתר-העיר/תחבורה-ירוקה/amb-אשדוד-מטרו-בס/מפות-פריסת-הקווים-החדשה-מכל-רובע/

Municipal network map by neighborhood; manual page retrieval was unavailable during this check. Cross-reference as historical/topological context only.

## Passenger-facing comparison
https://moovitapp.com/index/he/תחבורה_ציבורית-אשדוד-Israel-city_7-1

For manual user-journey comparison and naming only. Do not scrape proprietary route data, reuse their maps or claim live ETA from this page. Page retrieval was unavailable during this check.

## Validation protocol
1. Read current GTFS lines and stop sequences for Ashdod from `data/network.json`.
2. Compare route numbers and direction/terminus with operator map, flag disagreements.
3. Check that every user-facing stop code exists in the current GTFS and pickup/dropoff is allowed.
4. Treat 2022 PDF map and other dated maps as historical until confirmed by current operator notices.
5. Report **recognized search**, **valid route found**, and **complete directions** separately.
6. Never fabricate a service just because an older map shows a line.

## Known unresolved issue
The current app still cannot verify house numbers. A source map of bus routes cannot solve address geocoding. Address-level input requires verified coordinate source or an explicit user-selected nearby stop.
