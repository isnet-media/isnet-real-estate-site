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
