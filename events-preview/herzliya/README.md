# מה עושים בהרצליה

Public URL: https://isnet.co.il/events-preview/herzliya/

The Ashdod frontend is the canonical presentation source. `sync_event_city_views.py` includes Herzliya; `herzliya_city_view.py` holds the edition adaptations. All dated occurrences, movie sessions, restaurant records, guide entries and source photographs are Herzliya-owned. Existing health content is retained.

`herzliya-events.yml` refreshes the sources daily. The collector retains exact dates and source URLs, merges alternate seller links, preserves future records when a source fails, and rejects suspiciously empty replacements. The municipal calendar, hall, cinematheque, FRIENDS and Mevalim are parsed. Institutional and culinary directories without parsed dated entries remain explicit source links; no dates are invented.

Cinema combines local sessions with film-only editorial metadata; program suffixes such as שלישי זהב and ללא תשלום למנויים do not create separate movie cards. Reviews and audience scores appear only where the shared verified film registry has them. Official trailers are taken from the cinematheque's film page.

Restaurant imports require a structured Herzliya address. Sources include the restaurants, Rest, ROL, Easy and Ontopo. Source photographs retain URLs and credits; missing photography is not presented as a verified venue photograph. Unknown kosher status and Saturday opening remain unknown.

Checks: `python scripts/test_herzliya_events.py`, `python scripts/test_herzliya_health.py`, JavaScript syntax checks, and browser inspection of homepage, cinema, movie, seniors and culinary routes.

## Direct senior and Glilot coverage

`collect_herzliya_seniors.py` collects the municipal 65+ category and the community centers' senior calendar directly, reconciling occurrences with the existing feed. It also builds a separate recurring catalog from 2026–2027 community classes, reviewed club contacts, the older Beit Hagimlai program and service directories. Older Wix program prices/times are not presented as current; NDE is a directory link, not individually verified center records. Child-only titles do not receive senior audience membership.

`refresh_herzliya_city_cinema.py` verifies the official Glilot branch identity and each session's branch payload through Cinema City's public visitor CMS. The UI labels this venue as Glilot near Herzliya, separately from the local cinematheque. Failure retains the prior successful snapshot and its original verification timestamp.

## Cinema loading performance

The homepage carries a compact cinema bootstrap, excluding full sessions and long editorial detail. The original `cinema.json` remains authoritative for movie details and booking links. Israel-day formatters are reused, redundant cinema draws are skipped, and the hidden event board is not rendered while the cinema panel is open. Twenty-four films paint initially; filters and “more films” retain access to the full catalog. Verified promotional posters are served as same-origin JPEG thumbnails in the listing. Optional shared editorial data no longer blocks the movie detail screen.

`node scripts/test-herzliya-cinema-speed.cjs` checks exact film/schedule parity, a sub-30% compact payload, no network dependency for the inline cinema feed, no hidden event-board rendering and clock-cache refresh.
