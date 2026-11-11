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

## Verified actual public rollback, 11 November 19:25 UTC

Workflow43086524902/job130752238395 completed successfully. Public
super-delivery-status.json returned cities=[], data_bytes_offloaded=0 and
html_pages_routed=0. The original KGAT/data/catalog.json again returned31,293
products, nine branches and original retrieved_at2026-11-11T12:49:38.924043+02:00.
The original comparison HTML contained no data-super-delivery marker. After a
browser reload the rice comparison still showed all nine branches and the saved
item remained at quantity1. Source news release e1e49572ca718c2d8c3837ac72ba93fb191e72b6
and original run43023085987 were retained throughout pilot and rollback.

## All seven cities deployed, 11 November 19:30 UTC

PR72 merged as e79a747f410e15f4e7791194c47c9accb1f2b008. Workflow43087366998,
job130755161326, completed successfully. Public status independently confirms:
- data_bytes_offloaded:402,719,569; html_pages_routed:187.
- Pages artifact:405,262,258bytes, leaving594,737,742bytes below the1GB limit.
- Unrelated public files compared without editorial regeneration:7,782.
- Original news release marker remains e1e49572ca718c2d8c3837ac72ba93fb191e72b6,
  source run43023085987; supermarket migration run recorded separately.

The deployed native Worker is Site version14, commit9c673f1ac6d032d9aefa6cf2fb732e3793f0164f.
No full source-repository deletion or physical server migration is claimed.

## TLVNET build payload cleanup

The TLVNET source snapshot remains for reproducible preparation and recovery, but
scripts/strip-bundled-super-data.mjs now runs after every build and removes only
dist/client/super/data. The source public/super/data snapshot is untouched. Both
/super/data and/api/super-data routes continue through the independently hosted
service, with the existing public GitHub fallback. Build removal verified locally:
107files,45,481,796bytes. The release gate, frontend assets and reader lists remain
intact. A concurrent source-only economy/real-estate ledger update was preserved
by rebasing our packaging commit and rebuilding; no force push was used.

## TLVNET unbundling deployed and verified

Site version564 deployed successfully as appgdep_6af4c36436d08191a74167cc8d0add53,
source bd6f8039f61af70ddd1523ca519b9a0c1159dbf2. Its deployment archive contains
zero /super/data/ files, while the source snapshot remains present. Public
https://tlvnet.com/super-delivery-build.json independently confirms107files and
45,481,796bytes removed. Public/super/data/catalog.json returnsHTTP200 through
the Worker with X-Supermarket-Delivery:isnetsuper.ebs987449.chatgpt.site;
17,886products/19branches, original9November source date preserved. The
independent delivery does not mean every chain supplied fresh prices today.

Original public city roots for all seven cities returned the final migration
script and release lookup after deployment. Browser checks passed for KGAT
product comparison and list persistence across migration/rollback/full rollout,
Ashdod monthly basket/20branches, and TLVNET catalog/19branches. The added test
item was removed from the isolated browser at the end.

Remaining operational limits: source repository and original Git history are
shared; GitHub raw delivery remains an origin dependency; this migration did
not purchase or move to a new physical server. Existing daily GitHub collection
runners are separate from news delivery. The unrelated events integrity gate
still requires its own editorial resolution and was not disabled or bypassed.
