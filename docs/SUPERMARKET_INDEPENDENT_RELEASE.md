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
