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

## Anonymous read-only shadow canary and verified rollback — 2026-11-11

**This is not production cutover. The public city pages, collectors, DNS and
published price routing were NOT changed.** A tightly scoped shadow HTTPS route
was exercised and then disabled to prevent continued public serving or egress.

- On 2026-11-11, all seven `SUPER.*` Git trees on `main` were equal to their
  copies on PR #67's staging branch. This is a source-tree comparison, **not**
  a claim that suppliers delivered today's prices.
- A separate Edge Function `isnet-super-public-canary`, with
  `verify_jwt=false`, was deployed to the existing `isnet-ai-cms` project.
  Its live-data version exposed **only**
  `city=YAVNE&file=prices.json&release=5958cfaca9a61eacfdb1aa216635c3d3ff810850`
  from private Storage at the separate Supabase HTTPS URL, never via ISNET
  production city URLs. It had no media paths, asset directories, directory
  listing, user-selected Storage paths, or public service-role keys.
- The canary required the pinned manifest and checked **SHA-256
  `d0b3ffc01047f89bc08d34f652dc61de27cb16e4356db689594b2f824223072c`**,
  exact source byte length, JSON validity, and the original retrieved timestamp
  **2026-11-10T10:40:34.858582+02:00**; it returned explicit
  `X-Isnet-Preview-Only`, `X-Isnet-Snapshot-At`, `X-Robots-Tag: noindex`,
  and `Cache-Control: no-store` headers. It never labeled this snapshot as
  newly collected data.
- A real no-auth HTTPS test downloaded the Yavne JSON and verified `cmp`
  and SHA-256 against the committed original. The CI also confirmed CORS
  preflight, other cities/files/releases denied, POST denied, and anonymous
  Storage bucket reads still blocked. **CI PASS:**
  https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42984674737
- The fail-closed service variant was deployed and tested *before* the public
  probe (HTTP 503):
  https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42984602491
- **Immediately after the successful limited anonymous read, the Edge Function
  was rolled back to the fail-closed variant (version 3).** Verified externally
  by CI as **HTTP 503, no price bytes returned**:
  https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42984762002
  The private Storage bucket remains `public=false`. This proves a
  *shadow-route emergency shutoff*, **not** a production reverse-proxy rollback.
- The canary and shutoff sources are in
  `supabase/functions/isnet-super-public-canary/{index.ts,rollback.ts}`.
  The proof workflows are
  `.github/workflows/super-public-canary-check.yml` and
  `.github/workflows/super-public-canary-disable-proof.yml`.
  Do not interpret a past public-probe PASS as current availability:
  **the canary is intentionally disabled now**.

### Outstanding production gates

1. Serve **complete seven-city HTML/CSS/JS/fonts and permission-reviewed media**
   through a separately capacity-bounded public origin/proxy, resolving all
   existing relative URLs and ensuring TLS, CORS and mobile view parity.
   Media without confirmed publication rights must not be served.
2. Verify the incremental export of **only committed, approved collector output**
   from `main` to private Storage, preserving source age and skipping any
   unverified/failed source. Never introduce a second collection run.
3. Document and execute the real same-URL traffic cutover and immediate rollback
   for a low-risk city with a clean public baseline and asset checks. The
   shadow-route HTTP 503 drill alone is insufficient.
4. Keep PR #67 draft, Pages and current public site folders untouched until the
   production routing/rollback acceptance tests pass. No paid upgrade or DNS
   change was required for the shadow canary.


## Committed-source private JSON delta canary — 2026-11-11, 13:01 Israel

**New operational step completed (no publication/cutover).** The original seven
immutable private full-site releases and existing public Pages deployment remain
unchanged. Source collectors were **not** invoked by this release workflow.

- Inspected PR #67, seven independently built artifacts from run
  [42999910325](https://github.com/isnet-media/isnet-real-estate-site/actions/runs/42999910325),
  private bucket `isnet-super-staging` (`public=false`), and the live
  `main` supermarket data committed by the **existing** collectors.
- Live `main` now differs from the pinned private full-site releases in
  **ASHDOD, KGAT, YAVNE**. Read-only, seven-city source delta audit accepted
  these as *private candidates*, with no blocked cities; other four cities
  remain unchanged. Candidate commit:
  `155398161b347485831e41aec7cc4f081e099037`.
- Introduced `scripts/stage_super_committed_delta.py`, seven fail-closed unit
  tests, and `.github/workflows/super-committed-private-delta-canary.yml`.
  Workflow run
  [43008349721](https://github.com/isnet-media/isnet-real-estate-site/actions/runs/43008349721)
  **PASSED**, including seven safety tests and per-object private SHA-256 and
  exact-byte readback. The source-audit artifact is retained for seven days.
- Only **three critical committed JSON files** per changed city
  (`prices.json`, `refresh-status.json`, `source-status.json`) and a
  delta-manifest per city were saved under a separate, immutable
  `previews/committed-deltas/<city>/<source-commit>/` prefix. Storage SQL
  confirmed **4 objects per city / 12 total / 68,848 bytes**.
  This is a **data-only private delta**, not a complete site release, not a
  replacement for any of the seven pinned public-preview editions, and not
  permission to publish.
- The new source metadata explicitly reports **partial** coverage:
  ASHDOD **16/20** branches refreshed (Carrefour and Victory timeouts);
  KGAT **7/9** (Victory and Mahsanei Hashuk timeouts);
  YAVNE **4/7** (Carrefour and Victory timeouts). Older prices were retained
  for those branches, as documented in the original collector output.
  Every delta-manifest records the pinned baseline, exact committed Git SHA,
  original `checked_at`, coverage counts, `private=true`,
  `approved_for_public=false`, `public_cutover=false`, and
  `collector_invoked=false`.
- There were **no DNS changes, no purchases, no duplicate collection, no
  newly exposed media/fonts, and no change to live URLs**.
  The deliberately disabled public shadow canary remains disabled.

**Still blocked before public release:** full independent browser hosting and
media licensing, complete site-level cutover/rollback acceptance, safe and
validated production integration of *newer committed* prices, and a complete TLV
site (its committed index is a service-unavailable redirect). PR #67 remains
draft and must not be merged as a substitute for those proofs.
