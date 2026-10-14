# מעושרים באשדוד — pilot

This pilot is isolated on `meusharim-ashdod-v1`. Do not merge or deploy the repository's event site as part of this work.

## Public-source synchronization

Install Python `requests` and `beautifulsoup4`, then run:

```
python scripts/collect_meusharim_ironit.py --workers 3
```

The collector reads Ironit's public course filter (the same endpoint as its UI), unions all six age filters, and follows individual course pages. The all-results tab is the only inventory source: category-tab duplicates are not added. Source WordPress IDs remain stable and distinct groups with different source IDs remain separate courses. No guessed price, address, phone, enrollment availability, or district is published.

`--refresh` performs conditional GET requests for cached pages; without it, the cache resumes an interrupted import. Keep `.cache/meusharim` between syncs to preserve validators and avoid downloading unchanged pages. At most six requests run concurrently, starts are spaced by at least 500 ms. A failed detail page does not fabricate content; it remains marked as list-only and appears in `coverage.json`.

The source's public district and activity filters supply taxonomy associations. The source's course pages supply descriptions, schedule rows and direct registration links. A registration link does not mean open enrollment.

The activity taxonomy is stored as broad `category` plus precise `subcategory`. Age labels and every schedule row remain as published.

## Preview

Serve `meusharim/ashdod/` as the static root. `app.js` reads `data/classes.json`. Hosting configuration for the isolated private preview is stored in `preview.json`; this does not configure the existing events site's deployment.

## QA

`data/coverage.json` reports inventory counts, verification counts, errors, duplicates and field completion. `data/qa-sample.json` records a deterministic 20-course source comparison.

Missing fields remain empty and do not imply zero price or open registration. The UI loads 24 cards initially and supports additional results, free text, age, activity, district and individual weekdays.

## Homepage placements

The homepage renders only 6 curated placements from `ashdod/data/featured.json`. IDs, display titles and positions are independent of the collector; source refreshes preserve them. These are editorial choices, not a measured popularity ranking. Set `sponsored: true` for a paid placement to show the Hebrew "ממומן" badge. Never label a paid placement as an independent recommendation.

Homepage filters lead to `catalog.html` with URL query parameters for search, age, activity, subcategory, district, center and weekday. The full directory uses smaller standard cards and pages results in batches of 24.

The tennis homepage placement groups the public tennis listings at Beit Lavron and district D (Goldie). `source_ids` retains the group association and each `venues` entry links to the internal catalog filtered to that center, where original course schedules and registration links remain separate.

## Internal course pages

`ashdod/course.html?id=ironit-20211` renders one course using the public-source catalog. Descriptions, age groups, venue, district, instructor and schedule come from `classes.json`; unknown fields are omitted. Source schedule strings list the end time first, so the UI presents a left-to-right start–end range. Enrollment buttons retain the exact public-source `registration_url`, including the group parameters. Missing direct registration links lead to the source course page and are labeled as operator inquiry.

`course.html?id=tennis-ak` groups the 17 public tennis listings in the two user-selected venues, while each group has its own original registration URL. Regular listing titles, images and detail buttons open the corresponding internal page.

Design references reviewed: ClassBento's wheel-throwing detail page (photo, essential details, activity description and booking), and Yonkers Pottery's class schedule (age, times and enrollment).
