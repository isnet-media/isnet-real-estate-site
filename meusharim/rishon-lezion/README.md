# חוגים בראשון לציון

Public city edition: https://isnet.co.il/meusharim/rishon-lezion/

The initial catalog covers recurring programs in 23 municipal community centers
and their school branches. It is a catalog of programs at a location, not a count
of individual registration groups and not a complete directory of private tutors.
Facts come from the publisher's 2026–2027 brochures. Previous-year brochures are
excluded. The source URL opens the exact brochure page; enrollment is an inquiry
with the operator, not an assertion of availability. Unverified prices are omitted.
Schedule rows retain their age/group labels. PDF-extracted time ranges are ordered
start to end only when their duration is plausible; ambiguous rows are omitted.

Rebuild with Python requests and beautifulsoup4 installed:

```
python scripts/collect_rishon_classes.py
python scripts/build_rishon_classes_ui.py
node --check meusharim/rishon-lezion/app.js
node --check meusharim/rishon-lezion/course.js
```

`data/source-titles.json` is the reviewed set of exact source headings.
`data/coverage.json` lists the included centers, current brochure links and counts.
Photography is shared from the authorized activity bank, labeled illustrative,
and retains source provenance in `data/image-bank.json` and `source-images.json`.
No photo is represented as a photograph of the Rishon class itself.
