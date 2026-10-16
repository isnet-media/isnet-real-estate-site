# Events upgrade status — 2026-10-16

This is an implementation checklist, not a claim that every Base44 recommendation is complete.

| Recommendation | Implemented | Remaining / limitation |
|---|---|---|
| 1. Admin management | Full pagination, counts, search, filters, bulk changes and clone-as-draft | Live CMS permissions still govern access |
| 2. Controlled synchronization | Field locks, optimistic concurrency, central public-source comparison, browser baseline | Private editorial revision table/trigger is not installed; schema execution was declined. Revision viewing and load-into-editor UI is prepared. No live rollback verification |
| 3. Content quality | Missing fields, duplicate candidates, price conflicts, purchase-link audit; recent exact 404/410 ticket destinations suppressed in detail pages | Blocked/network-error checks remain unverified. No guessed replacement URLs; no automatic record deletion |
| 4. Direct event URLs | Existing event IDs and canonical slugs, reload support | Sample browser checks and full slug-generation parity; not a browser visit to every event |
| 5. Rich editing | Age bounds, end date, organizer, accessibility, contact, source, ticket state, locked fields | Depends on source data availability |
| 6. Search | Family/age/budget/date constraints, age clarification, grounded explanations, indoor/outdoor constraints, labeled alternatives | Unknown facts are excluded or labeled; not an external AI model |
| 7. Performance | Compact listing data, full data loaded on demand for search/detail, shared source/CMS requests, payload/gzip size report | No production stress test; no guarantee against outages. Older home fallback search uses listing text if conversation search is unavailable |
| 8. Returning visitors | Unified favorites, list sharing, ICS export, event sharing | Opt-in weekly email newsletter needs a mailing provider, subscription storage and sender configuration; no signup form is presented as working |
| 9. Analytics | GA4 event-view bootstrap fix and known property 292529666 configured | Latest configuration check reports missing GA4_SERVICE_ACCOUNT_JSON. No reporting credentials have been installed or fabricated |
| 10. Search visibility | Canonical URL sitemap generated from source plus published CMS corrections, robots sitemap reference, corrected offers schema | JavaScript-rendered event pages; social crawler prerendering and actual indexing are not claimed |

## External dependencies

- GA4: install a read-only service-account credential as the GitHub Actions secret `GA4_SERVICE_ACCOUNT_JSON`; grant that account Viewer access to property `292529666`. Do not paste credentials into chat or the repository.
- Editorial revisions: review and apply `events-preview/admin/auth/event-revisions-schema.sql` through an authorized database operator. Existing data is not a historical archive; baseline starts at installation. Then verify authenticated access, anonymous denial, revision creation and restore-into-editor before calling it live.
- Weekly email: choose/connect an existing mailing service and configure sender, consent, unsubscribe and delivery endpoint before enabling registration.

## Validation

- `node scripts/test-saved-list.cjs`
- `node scripts/test-ga4-view.cjs`
- `node scripts/test-event-sync.cjs`
- `node scripts/test-site-search.cjs`
- `node scripts/test-ashdod-pilot.cjs`
- `python scripts/test_public_event_assets.py`
- `node scripts/test-admin-management.cjs`
- `node scripts/test-admin-editor.cjs` (requires the repository's linkedom dependency)
- `python scripts/sync_event_city_views.py --check`

Generated compact feeds, sitemap, source history and build report are created in the Pages build from the latest checkout, rather than committing stale copies of large datasets. Failure to read published CMS data stops sitemap/build publication; source-history unavailability is reported explicitly without blocking unrelated frontend fixes.
