# Ashdod automatic event quality repair

The `Repair event quality automatically` workflow runs after the seven configured
source/image workflows complete (including failure), every two hours at :47 UTC,
and manually. It checks out current main under the shared event-data write lock.
No paid model, new credential or runtime code execution from event text is used.

Repairs are limited to:
- Subtypes from explicit title/source evidence with >=0.95 confidence, using the
  intersection of reviewed definitions and the current taxonomy.
- Missing media from a unique verified, publishable donor with exactly the same
  title and source detail URL. Old thumbnails are invalidated. Good media and
  manual image overrides remain intact.
- Missing stand-up clips from an exact artist/alias match in the verified shared
  catalog, verified within the last 30 days. Clips remain labelled representative.
- Byte-equivalent duplicate event records sharing the same ID. Conflicting IDs
  fail the batch; different events are never merged by name alone.
- Source-added taxonomy values without reviewed definitions are retained with
  `requires_mapping: true`. They cannot be used as approved subtype evidence.
  The definition validator still requires full coverage for reviewed taxonomy;
  quarantined ingress values no longer stop all approved classification.

Title, date, clock, venue, booking URL, primary category and publication state
are invariant. Field locks and manual overrides are checked before changes.
The source feed is changed; published CMS overrides retain their existing priority.

`automatic-repair-status.json` lists remaining findings and fingerprints all repair
inputs. `automatic-repair-history.json` retains exact field before/after evidence,
deduplicated by repair signature. Git retains previous versions. Validation runs
before a single commit publishes data, taxonomy, report and history together. On
push contention the worker starts again from current main; it does not force-push.

The admin page `automatic-repair.html` distinguishes a completed worker with open
exceptions from a healthy snapshot and flags reports older than three hours.
It shows the historical repair ledger and a filterable exception list. Source
errors, stale snapshots, missing cinema trailers, missing descriptions and
ambiguous media are reported, not turned into invented facts. Failed upstream
workflow context appears in the exception report and remains in Actions evidence.

A worker succeeding means its bounded pass completed, not that every event is
correct. It does not automatically research new images/videos, obtain missing
YouTube or GA4 credentials, change editorial descriptions, adjudicate conflicting
source facts, or claim live-browser verification. Those require separate source
adapters or verified research. The workflow emits an Actions warning and an admin
attention state while findings remain. It does not recursively trigger itself.

Validation: `python scripts/test_automatic_event_repair.py` covers locks, ambiguity,
freshness, exact-source media reuse, duplicates, idempotence and failure isolation.
`python scripts/test_subcategory_definitions.py` validates reviewed classification.
After deployment, verify the admin dashboard and independently sample changed
public cards. Do not close the earlier audit tasks based on worker success alone.
