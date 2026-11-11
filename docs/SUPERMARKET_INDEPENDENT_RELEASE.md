# Independent supermarket deployment: safe migration

This change introduces an **independent release artifact per city**. It does NOT yet
separate the live hosting target from the existing network Pages deployment.

## Why the live path is unchanged

- `pages.yml` still stages every `SUPER.*` directory and rebuilds supermarket data.
- The daily collector workflows publish vetted updates under existing ownership locks.
- No external supermarket hosting origin, CDN mapping, TLS certificate or rollback endpoint has been verified.
- Some URLs, such as `SUPER.TLV/index.html`, intentionally redirect to an existing city-domain service. Changing or deleting those paths before a documented hosting cutover could break links.

## Implemented isolation

- Each of seven cities creates its own immutable artifact and SHA-256 inventory.
- JSON is validated and files are copied byte-for-byte; no prices or dates are changed.
- Each city artifact is independent of all other supermarket city datasets.
- PR CI runs the same packaging tests, without invoking any collection jobs.
- The old Pages publication and all public links continue working untouched.

## Requirements before complete production cutover

1. Select independent storage/deployment target with sufficient capacity and availability, TLS and access controls.
2. Verify all asset references and price JSON requests from the city bundle at a staging URL; retain existing canonical paths.
3. Produce verified backup and restore evidence of all released price data and media.
4. Route read requests through stable URLs (or a verified reverse proxy), with no mixed-content or CORS issues.
5. Switch one low-risk city only after live public canary checks; retain previous original as instant rollback.
6. Remove supermarket payload from news Pages artifacts and decouple price build steps **only after** verified new host public readback.
7. Preserve daily collector claims, freshness metadata, original prices and rights review. No duplicate jobs.

Never interpret an artifact-only CI success as a deployed independent supermarket system.


## Verified private-staging checkpoint — 2026-11-11

**This is NOT a production hosting migration or a public cutover.** PR #67
remains draft. The original Pages-hosted supermarket URLs, daily source collectors
and current-price publication are unchanged.

- Supabase project `qomkxhafrprooekwgsxf`, bucket `isnet-super-staging`:
  `public=false`. No storage ACL was made public.
- All seven pinned city editions have **complete private manifests** and
  the storage uploader verified SHA-256 by downloading every uploaded object.
- Current complete pinned inventory: **1,292 source files / 434,500,361 bytes**:
  ASHDOD 200, YAVNE 192, KGAT 200, RISHON 201, HOLON 197,
  BATYAM 193, TLV 109.
- Six cities are stored under immutable release
  `5958cfaca9a61eacfdb1aa216635c3d3ff810850`; TLV is verified
  under `c674f83485453570106ce39a55c9c66f3a061ec3`
  (a second successful pilot TLV release also remains, not deleted).
- BATYAM staging initially stopped on an ambiguous HTTP 400 after 139
  objects, then resumed against the **same** immutable release. It finished
  with 193 files + one manifest; no price sources were rerun or overwritten.
- Artifact CI: `https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42970003924`
  built **7/7** independent city packages with SHA-256 manifests.
  GitHub artifacts are short-term backups expiring 2026-11-18; the verified
  private Storage releases are separate objects.
- Private migration/recovery CI:
  `https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42971084557`
  passed **7/7** cities on 2026-11-11. This check validates each private
  manifest against the pinned source, reconstructs **all 1,292 files** into
  throwaway directories from original Git snapshots and verifies SHA-256,
  reads `prices.json`, `refresh-status.json` and `source-status.json`
  privately for every city with matching SHA-256, and verifies that anonymous
  access to those private price objects is denied. No live restore was made.
- Original Git commits and active Pages edition remain available for rollback
  *before cutover*. A **live reverse-proxy rollback** remains unproven.

### Price-source freshness disclosure

These release contents mirror the Git price snapshot, **not a new collection**.
The latest `refresh-status.json` committed when staged reports 2026-11-10:
ASHDOD 20/20, BATYAM 19/19, HOLON 23/23, KGAT 9/9, YAVNE 7/7
branches updated; RISHON 17/24 and TLV 0/19 updated, with
`ConnectTimeout` on some sources and retained previous values.
Retained source data must **not** be labeled fresh. Reconcile more recent
collector commits before any eventual public traffic switchover.

### Hard gates before independent public serving

1. Introduce and test a safe, cacheable, read-only **public origin or proxy**
   that fetches from private Storage without putting any service-role key into
   client HTML/JS; bound requests and costs. The private bucket itself remains
   private.
2. Rehearse complete browser loading for each city's HTML, CSS, fonts, media,
   price JSON and relative URLs at an isolated staging route with TLS, CORS,
   mobile behavior and canonical SEO preserved.
3. Supply an **incremental update mechanism** driven only by validated,
   committed collector output (not an extra collector); guarantee stable
   versioned data and no source-date inflation.
4. Capture baseline public endpoint responses, then test a low-risk city via
   reversible same-URL routing, including rollback to existing Pages while
   verifying public readbacks and comparing price/refresh metadata.
5. Only after stable public cutover for **all seven cities** should
   `pages.yml` stop bundling those `SUPER.*` paths. Do not merge PR #67
   or delete the old files as a substitute for this proof.

No paid upgrade, DNS change, collection replay or live route modification was
performed to achieve this checkpoint.
