# Supermarket delivery isolation, 11 November 2026

Independent public read-only Worker origin: https://isnetsuper.ebs987449.chatgpt.site .
Native Site project appgprj_6ad8879811688191bdaaf7e7fa024a14, source commit
49acf1dfd4ba94657c61952abd5b1daa63b52c21. The service streams and caches public
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
