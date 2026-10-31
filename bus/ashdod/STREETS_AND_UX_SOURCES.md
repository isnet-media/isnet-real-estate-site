# Ashdod bus: street search and passenger UX improvements

## Approved street-name sources (not Moovit scraping)
- Official Israel street list: https://data.gov.il/datasets/population_authority/321 (CSV updated 2026-10-25).
- Official street-name synonyms: https://data.gov.il/he/datasets/population_authority/israel-streets-synom (October 2026).
- Filter official records to Ashdod using official locality code. Preserve official street IDs and original names; maintain aliases for abbreviations and alternate spelling.
- Verify actual dataset columns and licenses before ingestion. No guessed street-to-coordinate mapping. Street names alone do not locate a house number.
- Transit GTFS remains source of route stops, schedules, pickup/dropoff and station coordinates.

## Passenger UX lessons from Moovit reviews
Sources: https://play.google.com/store/apps/details?id=com.tranzmate and https://apps.apple.com/il/app/moovit-public-transport-live/id498477945?see-all=reviews
- Reviews repeatedly mention intrusive advertising, confusing screens, unstable location and inaccurate live ETAs.
- Keep core transit search free of interstitials; make one recommended urban result visible immediately.
- Separate **scheduled** from **verified live** arrival; no fabricated real-time claim.
- Always permit manual origin and destination entry; never assume GPS is correct.
- Show clear station identity/direction and a map link with readable labels.
- Show bus ride duration separately from wait time and walking estimates.
- If the user inputs a street without a verified house coordinate, label the result as street-level and offer stop selection, never pretend precise door-to-door.
- Display intercity alternatives only in intercity mode.

## Ingestion acceptance checks
1. Confirm downloadable official CSV and field definitions; identify Ashdod locality code from the official source, not memory.
2. Count unique Ashdod street IDs; test aliases and duplicate normalization.
3. Reject any row missing street ID or official name; retain update date and source.
4. Check ten representative street queries, including Hebrew abbreviations, apostrophes and punctuation.
5. Measure search recognition separately from routes actually found.
6. Test 390px mobile screen, 16px+ text, RTL keyboard, no horizontal overflow, and no blocking advertisements.

## Licensing
Moovit WebApp terms explicitly restrict scraping, bulk exporting and storing transit data for building a database: https://moovit.com/legal/webappterms/ . Do not scrape Moovit or copy its interface/assets.
