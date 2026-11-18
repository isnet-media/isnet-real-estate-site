# Infrastructure stabilization gate — November 2026

Scope: harden the existing ISNET/TLVNET network **before** enabling any new city.
Do not create HAIFANET collections, DNS, production jobs or publishing workflows yet.

## Verified code findings

- The Pages build stages public directories through `scripts/prepare_pages_public.py`, already has an exact 1,000,000,000-byte limit, and warns above 850,000,000 bytes.
- A previous operational report documents `syncing_files` timeout failures, while other deployments succeeded. The root cause is **not proven**.
- `actions/deploy-pages@v4` clamps timeouts to 600,000 ms. Increasing the YAML argument to 1,200,000 ms was ineffective.
- This PR adds a **read-only** payload size report for every Pages build. It does not archive, delete or migrate content, and does not claim to measure ClubVPS.
- The `tlvnet_agent_worker.py` has dedicated TLVNET prompts and a `tlvnet_agent_runs` queue. Do not point a second city at this worker or queue without isolated ownership and acceptance tests.
- `scripts/super_city_runtime.py` explicitly permits only YAVNE/KGAT/RISHON/HOLON/BATYAM/TLV; it is not yet a generic city registry.

## Release gates

1. **Deploy health:** Three consecutive successful scheduled or change-based Pages runs, each with an accessible `deployment-version.json` matching the deployed run, plus no unresolved `syncing_files` events in the observation period. Do not produce extra deployment traffic just to satisfy this gate.
2. **Multi-city agent isolation:** A separate test environment with distinct city IDs, queues and source inventories, verified claims and ownership locks, separate media rights evidence and cross-city contamination tests. No automatic public publication without existing editorial review.
3. **Server metrics:** Obtain actual ClubVPS CPU, RAM, disk usage/inode usage, bandwidth, peak concurrency, slow queries, backups and restore evidence over a representative busy period. Refrain from capacity upgrades without evidence; do not infer ClubVPS capacity from GitHub repository size.
4. **Media/data hygiene:** Compare staged public payload groups over time, document media provenance and last-good data, then plan a reversible migration for heavyweight assets; never delete originals before checksum and public read-back.
5. **Operational guardrail:** No concurrent collector duplicates; honor existing locks and source freshness. Fix only verified defects; revert if any regression appears.

## Server verification checklist (run only with authorized host access)

- `df -h`, `df -i`, `free -h`, `uptime`
- `ps aux --sort=-%mem | head -20` and equivalent CPU sampling during peak load
- Review reverse proxy access/error logs, response-time percentiles, disk growth and database metrics
- Check backup age, last successful restoration, off-host copy and available free volume

Record timestamps and host identities **without copying secrets or personal data** into this public repository. If the host cannot be accessed, label the server gate **unverified**.

## Explicit non-goals of this PR

No production domain change, extra agent or collector schedule, destructive cleanup, migration, server upgrade, or new city activation. Merging remains gated on CI validation and operator review.
