# Ashdod supermarket operations

Canonical site: https://isnet.co.il/SUPER.ASHDOD/ . Source: this repository,
`SUPER.ASHDOD/`. This is a static application on the shared ISNET Pages deployment;
it does not run inside the Ashdodnet CMS. Browser shopping lists remain local.

## Collection and publication

`super-prices.yml` claims one collection per Israel calendar day, starting at
06:00 local time (summer/winter UTC wake-ups plus delayed-scheduler recovery).
Later wake-ups skip a day already claimed, including failed attempts. Only registered branch IDs from the
catalogue are collected. `refresh_super_prices.py` uses official public file
portals; publishedprices accounts are retailer-provided public users with empty
passwords, not private customer accounts. No credentials are stored in source.

Full files are followed by all listed subsequent price deltas. XML branch identity,
publication date, source hashes, plausible product counts and finite prices are
checked before replacing any branch. Connections use bounded timeouts and retries, plus one focused recovery pass after
other branches finish, using at most four concurrent workers instead of serial
timeouts. The job allows 45 minutes and an active run is not cancelled by a new trigger. A failed branch keeps its previous prices
AND their actual file date. A failed fetch never becomes a zero price. A zero price
in a successfully parsed delta removes that observation. Publisher ItemStatus=0
is NOT treated as a deletion flag. Local short item codes are namespaced by chain.
No silent kg/package conversions. New branches require reviewed identity and
product equivalents. 100 ומעבר and העגלה הזולה remain pending direct source discovery.

The 21 October Shufersal file is bootstrap-only: it skips branches with newer
snapshots and must never roll back a live update. Its full-file metadata is
preserved. Collector timestamps identify retrieval, not when every shelf price
changed. `refresh-status.json` records each attempted branch separately.

After collection, fixed baskets, smart alternatives, promotions and all local
public links/assets are tested. Only a passing candidate is committed. Push is
non-forced, with a rebase against main; conflicts stop publication. Reports survive
as 30-day GitHub Actions artifacts even after failure. The Pages workflow listens
for successful collector completion, including commits produced by GITHUB_TOKEN.
Its own publication tests still run before deployment. A partial source collection
is logged as a warning; the independent public health check flags it as a failure.

Do not change basket quantities to force a historical budget. 600–700 ILS is a
selection target; genuine market movements may change the observed average.
If a reviewed comparison product disappears, keep its fixed line and quantity,
show the missing observation and exclude that incomplete branch from rankings.
A replacement still requires review. Do not fabricate a price or choose a
different unreviewed food type to pass the check.

## Monitoring and recovery

`super-health.yml` checks public core pages in all six cities daily and after a
successful Pages deployment, branch age (over one day), a missing morning
collection after 08:00 Israel (with the Saturday pause), and partial sources. It is read-only. GitHub Actions
failure notifications follow the repository owner's notification settings; the
ChatGPT monitoring task provides a separate user-facing alert path.

`audit_super_site.py` checks every current HTML page's local files, images, scripts,
links and fragment targets (including the app's hash routes). It does not claim a
complete visual/device audit or verify third-party destinations. Public health is
not the same as a successful Pages build. Review Actions and the public JSON after
publication. Three consecutive daily successful runs are the rollout gate for an
unqualified daily-refresh claim; do not assert that gate passed on setup day.

Code and committed data have Git history and the repository's daily bundle backup
workflow (seven-day artifact retention with restore verification). This is not an
independent off-account disaster recovery service. Recover via a reviewed revert
of the specific supermarket commit, preserving unrelated ISNET project changes.

Recipe prices remain a separately dated reference estimate; the current daily
pipeline does not claim to update recipe ingredient medians or recipe budgets.
Do not label those estimates with the collection date unless rebuilt and tested.

## Netto Chisachon, added 22 October 2026

The official Bina Stores file identifies chain 7290058156016, store 197 as
נטו חיסכון אשדוד, האורגים 13. Its first verified full price file contains 6,733
products. This is distinct from the former Haavoda 64 location, now 100 ומעבר.
The existing daily collector registers this reviewed branch and uses the Bina
connector; no second scheduled collector is introduced. Total connected: 20.

The shared family basket uses reviewed 1-litre canola oil, 550g sweet corn,
550g canned chickpeas and 600g frozen salmon equivalents. The baked-beans line
was removed from ALL branches because the new source reports conflicting pack
weights (550/580g versus the reference 560g); prices or weights are not invented.
All remaining quantities are unchanged. A missing promotion file is not replaced
by fabricated offers. Three complete daily collections must cover all 20 branches.

## City publication checks, 23 October 2026

City builders regenerate their own HTML and product-group assets as well as data.
Each city workflow stages its entire validated SUPER.<CITY>/ directory before
rebasing, so generated interface changes cannot leave a dirty checkout that blocks
publication. No unrelated city paths are included. Shopping-list regression tests
cover all six cities and preserve existing lists when trying the sample basket.

## 27 October 2026 repair

All 102 registered branches across the six cities were collected from official
27 October files in the connected workspace and passed local city publication
checks. The previous Actions runners reported transport timeouts for Carrefour,
Victory and other sources. Workspace recovery is evidence for this collection,
not proof that every future Actions runner can reach each source.

Namespaced offer shard names can contain `:`. Uploading the raw directory with
upload-artifact rejected those filenames and skipped otherwise validated data
publication. All six collection workflows now pack the evidence into tar.gz
before uploading it. Retailer-wide listings are shared once per collector run;
each download uses its own session with a copy of public portal cookies.

The hash-verified `.supermarket-repair` package and `apply_super_repair.py` restore
the validated collection without another source scan. Each city rejects any
unexpected concurrent base-file change and runs its normal checks before commit.
The monitoring automation now covers all six cities and all 102 registered branches.
Three complete scheduled daily runs are still required to establish stable daily
operation; a successful one-off recovery alone does not satisfy that gate.

## 4 November 2026 transport diagnosis

GitHub's official-feed probe (run 41777240461) found connection timeouts to
Carrefour and Laib (Victory/Machsanei Hashuk) on both Ubuntu and macOS runners,
and HTTP 403 from Hazi Hinam. Changing runner OS did not restore access.
The same first three directory URLs answered in the connected workspace;
that is not evidence of an automatic collection or deployed price recovery.
Do not route around access controls or substitute a different price source.

Failed retailer directory requests are now shared across branches as well as
successful ones. Only the existing focused recovery pass resets transient
connection/HTTP 429/5xx failures, once per directory. HTTP 401/403 refusals
stay cached for the run (including Holon's store-specific Hazi Hinam listing).
Reports retain the exception class and add HTTP status/host where available,
without tokens, cookies, signed URLs or fabricated source dates. This reduces
repeated requests; it does not remove a network restriction. Daily claims and
the last verified prices remain unchanged.

## Official-feed network recovery, 4 November 2026

Direct probes on both Ubuntu (Azure eastus) and macOS (westus) GitHub runners
confirmed Carrefour and Laib TCP timeouts, and Hazi Hinam HTTP 403. The same
reviewed official endpoints returned valid listings and files in the connected
Work environment. More retries on the same hosted-runner network do not fix this.

The existing daily maintenance task is the secondary recovery path. After the
normal collector finishes, run `scripts/recover_super_sources.py --city CITY
--raw-dir /tmp/official-CITY` in a connected environment only when source dates
are stale. This retries stale branches only, refuses Saturday or an active daily
claim, preserves healthy offers, and keeps the existing promotion selection.
Run each city's usual builder and deployment checks before publishing. Never
claim a recovery finished until public refresh-status.json and prices.json agree
with the candidate. The normal collector and its daily claim remain in place.

Publish a workspace candidate through the hash-checked `.supermarket-repair`
package and `apply_super_repair.py`: each file carries before/after hashes and
must reject concurrent updates. Partial recovery is allowed only with its actual
status/counts recorded in the manifest; it must never be relabelled complete.
A one-off recovery is not proof of reliable future network access. If both the
normal runner and maintenance environment cannot reach a source, report the
specific branch/date and preserve its real timestamp.

## Workspace recovery allowance, 8 November 2026

Start from current main and confirm no collector or publication is active. The
workspace recovery now requires today's completed/failed daily claim with its
finish timestamp, and refuses any started claim (including a previous day's
unfinished run). A same-day `stale_source_recovery` report also blocks a repeat,
including reports written before this guard existed. No new source request is
made when these checks refuse the command.

Before the first request, `data/recovery-attempt.json` records the Israel date,
selected stale branch IDs and started status. The allowance remains consumed if
the process fails or is interrupted; changing raw-dir does not reset it. A workstation-wide file lock serializes all city recoveries before taking the
daily allowance; a per-city file lock provides a second checkout-local guard.
Catalog/offer merges must run one city at a time to avoid memory exhaustion. Include
the attempt journal in the validated repair package alongside the public report
so later fresh-main checkouts retain the evidence. The workstation lock also covers different checkouts in the same temporary
filesystem; separate machines still require operator coordination.
Never remove this evidence just to retry the same sources. The next Israel day
allows one attempt after that day's normal collector has finished; Saturday is
still excluded. These safeguards add no schedule and perform no price collection
in their regression tests or in the Pages validation workflow.


## Monthly household basket, 4 November 2026

The public default is now `monthly`, an illustrative cumulative month of shopping
for 4-5 people with a 3,500 ILS design target. The 48 fixed lines live in
`monthly-family-basket.json` and are shared across all six cities. Quantities and
candidate priority remain fixed as market prices change; no multiplier forces the
total to match the target. This is not a statistically measured household average.
The existing small family and identical-barcode basic variants remain available.

Monthly products are NEVER dropped to improve branch coverage. Incomplete branches
keep all 48 lines and a null total, are visible as partial, and cannot win/lose.
Category totals are null when any line in that category is missing. Brands and
explicitly disclosed attributes can vary; fresh/frozen protein lines remain
separate. Egg alternatives preserve 120 size-L eggs in whole 12/30 packs; two Rami
Levi product names explicitly identify 12 eggs although source quantity 1 denotes
the retail package. Powder is one 2.5 kg pack, not a monthly 6 kg purchase.

The annual comparison is exactly twelve times the observed monthly gap, conditional
on unchanged quantities and price differences; never describe it as a forecast or
actual annual savings. Ordinary shelf prices exclude club deals, delivery and
travel. The UI shows source dates and complete-branch coverage. Run
`test_monthly_family_basket.py` after city builders; Pages enforces it before deploy.

## Tel Aviv shared pipeline, 9 November 2026

TLV uses the same official-feed collector via `refresh_tlv_super_prices.py`, with its own `.supermarket-runs/TLV.json` and `super-tlv-prices.yml` daily claim. The reviewed registry contains 19 physical branches (11 Carrefour and 8 Victory); ten legacy Carrefour IDs failed XML identity verification and are pending, not registered sources. Ramat Efal is excluded. The initial connected Work collection verified all 19 source dates as 2026-11-09, 17,886 products and 125,767 branch offers. This one collection is not the three-day stable-operation gate.

Canonical published data lives at `isnet.co.il/SUPER.TLV/data/`. TLVNET's `/super/data/` delivery bridge reads this data instead of requiring a full TLVNET build for each price refresh. Verify actual bridge deployment/read-back before claiming completion. Daily collection never uses the old bootstrap again once committed data exists. Preserve actual source dates and fail closed on offer/catalog delivery failures; do not combine current catalog rows with bundled Nov6 offers. The 3,500 ILS monthly basket remains incomplete (0/19) and must not be ranked or filled with invented prices. Family/basic baskets and smart comparisons are rebuilt from shared fixed definitions. Recipe references remain separately dated.

The existing hash-checked `.supermarket-repair` mechanism and city recovery adapters accept TLV. Do not rescan after a daily claim or recovery allowance is consumed. Work on Windows needs Python UTF-8 mode; the generic recovery locking code uses POSIX fcntl and requires a compatible connected environment. HTTP 401/403 must not be retried around. Public health now includes the actual TLVNET `/super/` URL and 19 reviewed branches, for 121 physical branches across seven city editions.
