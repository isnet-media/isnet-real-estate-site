# Ashdod supermarket operations

Canonical site: https://isnet.co.il/SUPER.ASHDOD/ . Source: this repository,
`SUPER.ASHDOD/`. This is a static application on the shared ISNET Pages deployment;
it does not run inside the Ashdodnet CMS. Browser shopping lists remain local.

## Collection and publication

`super-prices.yml` runs each morning at 05:10 UTC (07:10 winter / 08:10 summer Israel),
on demand and when collector code changes. Only registered branch IDs from the
catalogue are collected. `refresh_super_prices.py` uses official public file
portals; publishedprices accounts are retailer-provided public users with empty
passwords, not private customer accounts. No credentials are stored in source.

Full files are followed by all listed subsequent price deltas. XML branch identity,
publication date, source hashes, plausible product counts and finite prices are
checked before replacing any branch. Connections use bounded timeouts and retries, plus one focused recovery pass after
other branches finish. A failed branch keeps its previous prices
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

`super-health.yml` checks public core pages hourly, branch age (over one day), last
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
