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
If a reviewed comparison product disappears, the candidate fails coverage checks
until its replacement is reviewed. Do not fabricate a price or choose a different
unreviewed food type to pass the check.

## Monitoring and recovery

`super-health.yml` checks public core pages in all six cities daily and after a
successful Pages deployment, branch age (over one day), last
collection age (over 30 hours), and partial sources. It is read-only. GitHub Actions
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
