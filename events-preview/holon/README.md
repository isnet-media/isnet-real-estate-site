# מה עושים בחולון — מבית חולון נט

Public edition: https://isnet.co.il/events-preview/holon/

Holon-owned calendars, culinary inventory, UI and release checks. Uses ISNET's dark/gold visual language and its owned illustration bank. It does not relabel another city's events, venues, restaurant photographs or analytics stream.

## Data and sources

- `data/sources.json`: organizer, municipal, community, museum and culinary sources.
- `data/source-report.json`: per-source collection status, direct-link-only sources and individual restaurant checks. Interactive and failed sources are not represented as successful intake.
- `data/events.json`: exact dated local occurrences, booking URLs and media provenance. Unknown additional dates, prices, ages and openings are never inferred.
- `data/restaurants.json`: direct venue/booking sources plus Rest records whose structured address explicitly confirms Holon. Existing verified directory records are retained when a listing's rotation changes.
- `data/categories.json`: images for all categories and subcategories. Local JPG promotional images and labeled ISNET-owned generic illustrations cover every visible card.
- `data/quality-report.json`: held duplicates/conflicts. Primary organizer schedules take precedence for the same show and date.

Museum closure notices and restaurant exclusions are explicit. A linked operator or club directory is separate from an actual dated event. Unknown kosher status and Saturday opening are not included in affirmative filters. Sports directories link to the club; unsourced fixtures are not fabricated.

## Daily pipeline

`Refresh Holon events and culinary guide` runs daily at 03:35 UTC and supports manual dispatch:

1. `python scripts/sync_holon_events.py`
2. `python scripts/polish_holon_catalog.py`
3. `python scripts/build_holon_events.py`
4. `python scripts/test_holon_events.py`

Only Holon data/media/generated pages are committed. The existing Pages workflow then publishes them. Source refresh failures retain proven data where supported and appear in the report. The release workflow verifies city isolation, all JPG files, categories, cuisines, mobile widths 320/390, desktop, search, date filters, dialogs, sharing and calendar downloads. Main pushes also verify the live release.

Edit `template.html`, `app.js`, `style.css` and city data, then rebuild; `index.html` and the main category aliases embed a fast static bootstrap. There is no dependency on a signed-in CMS request to show the list. WhatsApp, Facebook, email, clipboard and native sharing are available with a city-specific JPEG preview.
