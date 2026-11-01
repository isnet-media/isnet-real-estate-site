# מה עושים בחולון — the shared ISNET event edition

Public URL: https://isnet.co.il/events-preview/holon/

Holon uses the canonical Ashdod frontend through `scripts/sync_event_city_views.py`, including the homepage hero, discovery menu, free search, calendar, category rails, event detail pages, kids and seniors hubs, cinema panel, places, Saturday guide, and culinary layout. Edit the shared Ashdod presentation source; Holon adaptations live in `scripts/holon_city_view.py`. There is no separate Holon homepage UI.

`build_holon_events.py` adapts the city-owned raw feed to `data/events-public.json`, preserving original event IDs, dates, locations, booking destinations and image credits. It also builds Holon's own movie schedules and directories. No other city's events, places, restaurant photographs or analytics stream are copied. Common owned illustration banks may be reused with visible attribution.

The daily `Refresh Holon events and culinary guide` workflow collects city sources, polishes reviewed metadata, builds the normalized data and canonical views, and runs quality checks. The shared UI synchronization workflow also includes Holon so future layout changes propagate automatically. The culinary HTML, CSS and renderer come from Ashdod, with only city text and Holon venue data substituted.

Sources and limitations remain explicit in `data/source-report.json` and `sources.html`; interactive sources are direct links, unknown prices/openings are not fabricated, generic images are labeled, and museum closure notices remain visible. Local raw feeds and source/media provenance are retained.

Release checks cover raw/public ID parity, photo files, data isolation, exact shared CSS and calendar/rail bundles, the actual homepage shell compared with Ashdod, 320/390px and desktop layouts, search, detail pages, sharing, kids, seniors, cinema, food and local attractions. Live checks require the canonical layout marker and normalized feed.
