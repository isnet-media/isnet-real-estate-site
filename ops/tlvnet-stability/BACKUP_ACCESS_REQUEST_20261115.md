# TLVNET backup access request — pending approval

Only TLVNET.COM. No DNS, other sites, paid services, security expansion or new controller.

## Verified current access
- Sites source repository read/write is available; it is not D1/R2 service access.
- Owner-signed-in manual full export works; the platform service bearer does not supply owner identity.
- Wrangler reports not authenticated. No Cloudflare/R2/backup/vault environment credential names are present in the current executor.
- Existing runtime secret names are agent bridge, social encryption and social scheduler. None is authorized by the backup route.
- Cloudflare dashboard presented sign-in; account service identities, quotas and entitlement cannot be inventoried without authenticating to the account actually hosting the Worker/D1/R2. DNS account access alone may not be sufficient for Sites-managed hosting.

## Exact proposed approval (not implemented)
Authorize one dedicated backup service principal for TLVNET only, limited to GET inventory/schema/table export and ETag-pinned object reads through /api/editorial-backup. Deny every write, publishing, social-send, membership, runtime-secret export, DNS and other-site route. No account-wide Cloudflare key, Global API Key, existing social token or agent token reuse. At most one encrypted full snapshot daily within the existing controller cycle, bounded attempts and last-good preservation. Proposed retention: 7 daily and 4 weekly snapshots, only if existing storage allowance is confirmed; no paid purchase. Store the verifier in hosted secret configuration; store the token in an approved runner's vault, never source, prompt, URL or report. Record only key ID/expiry/audit events. A separate writable offsite destination scope must be confined to its backup prefix and cannot grant production writes.

Approval wording: I approve a dedicated TLVNET backup identity with the read-only application scope above, installed in an approved existing unattended runner; no wider permissions or new cost. Approval alone does not supply the runner/vault connection.

Required owner action: authenticate the actual hosting account or enable the hosting provider's supported resource/service access; identify/connect an existing unattended runner and vault that can inject secrets securely. If these are unavailable, stop this access path and retain manual encrypted recovery; do not invent a persistent service credential in a task prompt. Cloudflare account-wide D1 read credentials may not authorize export operations; verify supported exact API permissions before proposing any native token.

## Three missing operational secrets (values prohibited here)
| Name | Function | Recovery requirement |
|---|---|---|
| TLVNET_AGENT_TOKEN | Server-to-server authorization to the TLVNET Supabase agent bridge | Preserve original value and corresponding bridge configuration; missing value prevents bridge calls, not static reading. |
| TLVNET_SOCIAL_KEY | AES-GCM key for the encrypted Meta connection stored in R2 | Original key is required to decrypt existing connection backups. A newly generated replacement cannot decrypt them. |
| TLVNET_SOCIAL_SCHEDULER_KEY | Authorization for the scheduled social-run endpoint | Keep matched to the existing scheduler client. Do not reuse for backup or change during restoration. |

Store original values directly from the original secure provisioning source in an owner-controlled encrypted vault, under TLVNET/production and dated versions. Limit recovery access to the owner and explicitly approved recovery operators, retain version history, and keep a separately protected recovery method. Do not paste values into ChatGPT, files in source control, logs, prompts or browser URLs. The encrypted backup file's recovery key is separate from these runtime secrets and does not replace them. Current Sites tools return masked values, so no original secret values were recovered or fabricated. If the encryption key is lost, recovery of the original encrypted Meta session is not proven and reconnection requires a separate controlled action.

## Isolated running-site restore procedure
1. Verify backup digest, source commit/deployment manifest and snapshot timestamp before extraction.
2. Restore into new isolated D1/R2 or local test resources, never production bindings. Apply schema/tables first, insert snapshot records, then recreate indexes/triggers; verify counts, integrity and media digests.
3. Use the exact source commit; restore media metadata and static assets. Validate all public content variants plus social/queue records.
4. Disable cron/social sends, AI calls, webhooks and external writes in the staging environment BEFORE injecting secrets. Default deny outbound network; do not rely only on UI flags. No production tokens in routine staging fixtures.
5. If real integration restoration must be validated, approve narrowly scoped outbound allowlists and read-only checks separately. Do not send a post or claim queued work to prove recovery. Test keys/doubles are sufficient for failure-path tests but do not prove real credential recovery.
6. Start only a supported isolated runtime, verify pages/API/media and authorization. Measure end-to-end RTO including provisioning/download/start; measure RPO against the newest fully verified scheduled snapshot. Current 0.207s local data restore is not site RTO.
7. Retain production unchanged; document whether every gate passed. Never start seven-day qualification with missing gates.

## Capacity and cost decision
Existing resources support offline handler/SQLite/file integration tests without cloud traffic or new purchase. Completed 320 handler requests at concurrency1/4/8/16; all200. Eight same-job attempts produced one upstream call and seven409conflicts; provider-down job was retained, public reads continued, retry recovered. This is NOT a hosted Workers/D1/R2 or quota test. Account credentials, resource IDs, plan usage/billing and supported isolated hosting are unavailable. Do not provision a second public Sites production URL as staging or assert free cloud entitlement. Approval for payment is not requested because no priced requirement has been established.
