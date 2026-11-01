# מתי יש אוטובוס? — קריית גת

Public route: https://isnet.co.il/bus/kiryat-gat/

A city-specific edition of the Ashdod bus planner, retaining the same responsive CSS, direct urban recommendation, large departure time, maps, explicit station choice for unverified addresses, sticky navigation and rich sharing. Local destinations use only named official GTFS stops: the rail terminal, central bus station, Karmei Gat terminal, BIG, Gat Center and National Insurance. The source locality is `קרית גת` (Population Authority code 2630); display branding is קריית גת נט.

Bus schedules are extracted from the complete official national GTFS feed, preserving routes that serve Kiryat Gat and their full relevant stop sequences. Rail alternatives depart separately from the actual rail station (GTFS ID 37316), and clearly exclude access time to that station. No Ashdod-local landmarks, origin stops or rail origin are carried over. Street names and alternate names come from the current Population Authority datasets; missing named-stop linkage is not treated as proof of no nearby service. House-number coordinates and live arrivals remain unavailable, exactly as in the Ashdod version.

Daily workflow `kiryat-gat-bus.yml` refreshes bus, rail and streets, generates the coverage audit, tests the datasets and commits validated output. The Pages workflow subscribes to its completion so bot data updates are deployed. The new city collectors are parameterized separately, preserving the existing Ashdod pipeline.

Validation: `node --test bus/kiryat-gat/*.test.cjs`; `node bus/kiryat-gat/browser-smoke.cjs`; `node bus/kiryat-gat/production-smoke.cjs`.
