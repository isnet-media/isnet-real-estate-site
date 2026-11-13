# ISNET / TLVNET — deployment and migration contract (draft)

**Version:** 2026-11-13. **State:** NOT DEPLOYED / NOT ENFORCED. This is an isolated review branch; it must not trigger publishing or change existing timers. The accompanying JSON is a design contract, not proof of runtime enforcement.

## Authority and isolation
- TLVNET uses its own Sites publisher; ISNET uses the CMS with website/category lookup. Never deploy ISNET GitHub Pages onto TLVNET.
- Flash 90 is permitted only for TLVNET where a specific valid license allows that exact use; prohibit its assets and derivatives on ISNET. For each destination store image license, rights holder, source, usage scope, credit and asset hash. Never infer that web permission includes social permission.
- City agents must use their own municipality, municipal corporations, local media and nationally sourced stories with verifiable local relevance. International multilingual research is permitted for future/culture magazines; translate accurately and paraphrase, with original fact-checking.
- Herzliya and Raanana require independent city editors, but do not resurrect cancelled automations without verifying the actual owners, pending approvals and existing local root tasks.

## Publisher contract
Research and drafting can proceed concurrently. For publish: acquire durable target-scoped lock with lease and compare-and-set semantics; verify actor and grant; publish once; read back public URL, metadata, image and credit; release only owned lease. Do not alter another actor's lock. On busy target, checkpoint and queue instead of retrying or overwriting. Human/legal/rights/accuracy approval gates remain intact. Preview-only failure may permit a clearly logged exception with deferred post-publication visual review only after other integrity checks succeed.

## Cost and runaway protection
Enforce in executable runner, not just prompts: one discovery pass per cycle; idempotency keys (agent,target,content fingerprint,cycle); content/source caching; finite attempts (initial + one conditional retry if failure cause or inputs changed); hard elapsed-time and API-spend limits; per-domain and per-model concurrency caps; circuit breaker keyed by normalized failure; persistent checkpoint and next scheduled recovery. No recursive self-scheduling, subagents per cycle, duplicated build/deploy just for log writes, or calls in an unbounded while loop. When AI budget is exhausted, continue deterministic ETL, cache refresh and safe preapproved publication, but do not fabricate AI output.

## Content quality
Each writer owns discovery, editorial prioritization, writing, rights-checked image (or distinctly labeled AI illustration), SEO, publication and live verification. Write lively original reporting with distinction among verified fact, analysis and opinion; no invented quotes, sources, interviews or first-hand reviews. When no new hard news exists, use sourced interpretive analysis or locally grounded feature only if newsworthy. Specialized statistics agents update figures and mobile layout with source dates without faking a new content date.

## Rollout steps and hold points
1. Inventory Work tasks, ChatGPT automations, GitHub Actions, Sites, CMS, server crons and locks; capture exact source-of-truth and owner for each.
2. Verify no duplicate publisher per section or destination and record exact prior schedules.
3. Implement actual budget / lock enforcement in each live runner and add automated failure simulations; this JSON alone is insufficient.
4. Pilot TLVNET news with single publisher, then Herzliya and Raanana after owner approvals. Check image rights and public readback.
5. Gradually migrate each scheduler off Work. Do not disable old path until verified output from new runner, then disable the old producer without deleting historic logs.
6. Only declare Work-independent after timed runs succeed without using Work or its credit bucket and there is a verified rollback route.

## Acceptance tests
- Two simultaneous publishes to one target: only one succeeds; other checkpoints.
- Preview failure: content can publish only if independent integrity/rights checks pass; visual check remains pending.
- Repeated network 403: one bounded retry only with changed condition; no loop and no expanded permissions.
- Rights misuse: Flash 90 assets rejected on every ISNET destination including cross-posts.
- AI quota exhausted: deterministic tasks continue, AI-dependent tasks checkpoint.
- Failure cannot disable entire unrelated task; no resumption of cancelled tasks.
- Published status requires public URL and verified readback, not merely a green workflow.

**Approval boundaries:** no new paid service, credential rotation, production DNS/R2/DB mutation or disruptive cutover without explicit approval; normal source changes can be reviewed in a PR first.
