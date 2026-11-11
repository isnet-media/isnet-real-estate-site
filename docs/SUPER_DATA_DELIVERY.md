# Supermarket delivery isolation, 11 November 2026

Independent public read-only Worker origin: https://isnetsuper.ebs987449.chatgpt.site .
Native Site project appgprj_6ad8879811688191bdaaf7e7fa024a14, source commit
9c673f1ac6d032d9aefa6cf2fb732e3793f0164f (Site version14). The service streams and caches public
committed supermarket snapshots from the existing collector repository. It runs
no collectors, accepts no writes and holds no CMS or database credentials.

The daily GitHub collector jobs, city locks and publication checks remain intact.
This removes duplicated data from the news Pages artifact, not the original Git
repository or its history. GitHub remains a source dependency; this is not a claim
that storage, source control and collection now have three independent providers.
The old private Supabase staging bucket remains private and is not this origin.

## Public cutover and compatibility

`prepare_pages_public.py` omits selected `SUPER.CITY/data/` directories only from
the Pages upload. It retains original HTML/CSS/JS/images, links, analytics and
browser origin, so shopping lists in localStorage remain on their original origin.
A script placed before page scripts routes only same-origin selected-city data
fetches to the independent origin, pinned to the exact source commit. Data-file
links are similarly routed on click. Other network requests are untouched. There
is no global storage clearing, frontend redirect, collection or price editing.
Direct legacy JSON URLs are no longer provided by Pages for migrated cities;
external consumers must use the independent data endpoint. Old cached HTML may
need one reload after the cache expires; do not remove all frontend files.

`super_delivery.json` is the reversible city selector. Empty cities restores the
original payload. Keep the independent origin available when rolling back: cached
routed pages may still refer to it. Verify source timestamps; a deployment date is
not a price-source update. Newly added public data filenames require updating the
Worker allowlist; existing offer shards and the catalog are supported.

## Separate storage-only release

The normal news Pages release is currently stopped by unresolved event occurrence
candidates. Do not disable or weaken those gates. `super-delivery-cutover.yml`
uses the exact artifact of the last successful public release, verifies its
commit/run against the live deployment marker, and changes only supermarket data
routing. `verify_super_cutover.py` compares every other file byte for byte; it
cannot publish new news or events from main. Existing deployment source metadata
is retained and supermarket migration metadata is appended separately. The job
uses the same Pages concurrency lock as the normal publisher and fails if another
editor's public release moved. It keeps the baseline archive for 30 days.

Each cutover first compares catalog/source-status/one offer shard bytes against the
same immutable Git commit through the independent public origin. Tests cover nested
pages, Request inputs, untouched news/external requests and exact local rollback.
After the pilot is actually live, verify the original public URL, comparison and
basket, run a real rollback and verify restored data, then enable other cities.
The city-selector config must point to a retained baseline artifact before the
initial original Pages artifact expires (12 November 2026, 12:47 UTC).

Tel Aviv has its own frontend at tlvnet.com/super. Update its data proxy to prefer
the independent origin before offloading SUPER.TLV/data from Pages. Do not redirect
the Tel Aviv frontend back to the placeholder source index.

No new billing account, purchased server or public database bucket is required.

## Live pilot and recovery evidence

- PR68 removed duplicated data builds from the news publisher; collector jobs retained.
- PR69 stopped before public deployment on a fragment-without-head guard.
- PR70 corrected fragment handling. Cutover run 43085505677 succeeded: KGAT
  data_bytes_offloaded=36,897,871, html_pages_routed=31. Public original comparison
  URL returned nine rice offers with source dates 10–11 November; one item was
  added to the isolated browser list for post-rollback persistence verification.
- TLVNET public Site version563 (source d3f2ff7e6b1cc6fa9b2997c3080d60ae10249ef7)
  now prefers the independent origin. Public response X-Supermarket-Delivery
  confirms that origin. Browser shows 17,886 products/19 branches, source 9 November;
  the migration does not claim these prices are fresh today.
- The public release pointer is .supermarket-delivery/release.json. The publisher
  runs on successful collector workflow_run events as well as direct data pushes;
  it checks committed JSON through the independent origin and commits only the
  pointer. No API branch lookup is needed. GitHub raw delivery is still a service
  dependency. Each browser page resolves the release once and keeps that immutable
  commit for its requests, with its build release as fallback during lookup failure.

- PR71 release publisher ran successfully as workflow43086525028/job130752239885;
  all seven city samples verified before publishing the immutable pointer. Worker
  /release subsequently returned b516ff99f5113c342dc13c03b5ad8e7629b10024,
  demonstrating automatic release discovery without a separate Site deployment.
- Full rollout must only merge after public rollback workflow43086524902 succeeds
  and the original catalog and browser shopping-list item are verified. The full
  selector includes all seven cities; retains only UI/static assets on Pages and
  moves the data delivery bytes. Baseline is already retained for30days, so
  subsequent cutovers reuse it instead of uploading redundant backup copies.
