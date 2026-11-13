# ISNET operations controller

Publisher mandate, 13 November 2026: diagnose and repair within existing authorized access, preserve publication continuity, learn from recurrence, and propose a specific human action for configuration, credentials, supplier or access failures.

## Coverage and limits

The controller runs once per hour around the clock. GitHub `Record operation failures` captures completed failed/timed-out/action-required runs into this existing ops area without an AI call. The scheduled controller also reads Actions directly: GitHub limits workflow_run chain depth and events can be missed. Capture is not diagnosis or a completed repair. Sites deployment failures and ChatGPT task results are checked through their own connectors; they are not all covered by the GitHub event inbox. The available Gmail connection is news@isnet.co.il; it did not contain the publisher's GitHub notifications. Do not claim access to another mailbox. No promise of immediate repair or prevention of every future failure.

## Source map

- Repository: isnet-media/isnet-real-estate-site; default branch main. Public site https://isnet.co.il. Core publication: .github/workflows/pages.yml and scripts/prepare_pages_public.py. Public deployment-version.json is actual deployment evidence.
- Event integrity: events-preview/shared/event-overlay.js, shared/data/event-quality-media.json, scripts/test-event-integrity.cjs, scripts/audit-event-integrity.cjs. Preserve old IDs, distinct dates/times/venues/casts, locked human decisions and rights. Never fuzzy-merge to turn a test green.
- CMS overlays: events-preview/shared/public-cms.js; use existing service connectors and published records only. Read required Supabase instructions before database work. No schema/RLS/permission changes under this mandate.
- Supermarkets: scripts/super_schedule.py, super_daily_run.py, check_super_public.py and seven .github/workflows/super*-prices.yml. Real collection only Sunday/Tuesday/Thursday 08:00–10:59 Israel; public supermarket health only those days before noon. The controller must not collect or fetch large price catalogs outside those windows. Metadata and job-status checks are separate.
- Sea: scripts/refresh-ashdod-sea.mjs, its tests and .github/workflows/ashdod-sea.yml. Regions 213 and 210 differ. Reject expired/future-only periods for a current widget; retain authentic last-good dates. Never publish stale data as fresh.
- TLVNET https://tlvnet.com: existing Sites project appgprj_6aeb3c238d748191bf82c9cd9c653c32. Read Sites instructions before opening current Git source; get audience, ownership and deployment status. Source is separate from the public GitHub repository. Never deploy this repository over TLVNET. News source: public/news/agents/*, articles.json, photo policies/requests and image presentation registry.
- ISNET admin: discover websites then categories before any post operation. Do not assume credentials or authority for a city from another site.
- Existing historical context: ops/REPAIR_2026-11-10.md, ops/AUTOMATION_EFFICIENCY_2026-11-10.md, ops/maintenance and ops/daily-audit. Older daily/hourly schedules in these files are superseded by current publisher decisions.

## Work cycle

Read state.json and incidents.json, then inbox entries and results after the saved watermark. Retain pending run IDs and revisit their completion regardless of creation-time watermark; paginate new metadata until the prior boundary and retain an overlap for same timestamps or delayed completions. A first page alone is not a complete backlog check. Reconcile actual run ID, attempt, source SHA, failed job/step, source mode and current status. No inference of live success from completed or green skipped work. On the initial retrospective review, investigate the preceding seven days in bounded pages; checkpoint the remaining backlog instead of claiming full coverage.

Group identical failures by subsystem + workflow/step + normalized cause + relevant source fingerprint, retaining every occurrence/run link. Read full logs only for new or changed fingerprints, redact credentials and personal data, and store minimal evidence. Skip unchanged known blockers after reporting them once; re-open only with changed inputs, access, source or a genuine recurrence after a verified fix.

Before editing, open fresh source and preserve concurrent work. Check real ownership/locks and deployment status. The publisher's content release takes priority. Do not unlock a writer, force-push, kill its deployment or overwrite it. Defer controller edits to an isolated branch/checkout, record the competing run and recommend a permanent ownership fix. Already approved content may be released through its established owner/source path; never invent an approval or publish unverified text to satisfy priority.

Use one diagnosis attempt plus at most one materially justified correction attempt for a single incident in a cycle. Repair safe code/configuration within the user's mandate, add a focused regression check for recurring defects, run relevant tests, and publish one change if needed. Avoid builds for journal-only changes and repeated whole-site audits. Verify actual terminal deployment and the affected public URL/data/image/credit; status fixed_verified requires evidence. If another blocker appears, preserve the partial fix and record what remains.

News agents must remain enabled. A preview-only failure does not block an otherwise verified article: apply the publisher's 13 November instruction, retain real source/rights/body/asset checks, record unavailable desktop/mobile preview and pending post-publication visual review. No fabricated visual approval, baseline expansion or bypass of access/build/content checks. Other unsafe publication failures affect the item, not the whole news agent. Do not resume cancelled tasks or change writer schedules without current authorization.

For missing credentials, permissions, billing, provider data, ambiguous editorial decisions or a failure beyond the code, report the exact missing item, evidence, impact and smallest next action. Do not buy credits, obtain new keys, expand security access or contact third parties automatically. Keep the controller active for independent incidents; do not create other agents or automations.

## Durable evidence and reporting

Maintain incidents.json with status open, mitigated, awaiting_external_action, fixed_verified or regression; root cause, change, relevant tests, deployment/public proof, prevention and occurrences. Maintain state.json watermarks, unresolved queue and history backlog. The event recorder owns immutable inbox entries; the controller updates incident state rather than erasing them. Store no secrets or raw email bodies. Ops-only changes must not trigger a public deployment.

Notify the publisher only of a material new incident, verified repair, significant collision or a specific action needed. Say what broke, what was fixed, what was verified and what remains. Do not repeat unchanged alerts. Provide practical prevention recommendations tied to observed evidence. The mandate is ongoing; a successful repair does not complete the controller's overall role.

## Authorized fallback for bank-control reads — 13 November 2026

A failed public fetch does not prove the live bank is down. When existing native Sites database read tools are available for the same owned project, use read_database_overview first, then the exact returned binding/table names and bounded settings pages. Continue only with returned next_offset. Inspect only the photo-bank-control-v1 row/ID; do not persist unrelated values, secrets or personal records. This is read-only diagnosis, never authorization to modify DB, obtain keys, bypass a denied write endpoint or expand permissions.

Absence of the control row is meaningful only after complete ID-page coverage and checking the exact deployed API source. The current deployed control function defaults to enabled=true, blockedIds=[], version=0 when this row is absent. A present row may disable collection or block assets and always takes precedence. Recheck at publication time; this evidence is not an image rights grant, body/asset approval or a publication lease. See evidence/photo-bank-control-native-read-20261113.json. Do not treat the unrelated enrichment refresh lock, source CAS, schedule map or a terminal previous deployment as an exclusive publication lock. An isolated patch remains pending release until the existing release owner has valid ownership.

## Image URL ownership regression —13 November2026

The emergency mobile investigation reported a full-image/thumbnail src oscillation; the publisher confirmed recovery after removal of the conflicting upgrade snippet. This controller has not independently verified the mobile/app repair. Do not attribute the separate AdSense initialization error to that loop. Before reintroducing image URL normalization, keep one owner per image src, make normalization idempotent, and test native thumbnail rewriting plus image-error fallback until the src settles. Verify desktop and mobile paths separately. Coordinate with the existing emergency CMS owner; no parallel template rollback or fabricated visual sign-off.
