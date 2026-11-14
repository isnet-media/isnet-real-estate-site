# TLVNET Meta API connection — one-time admin setup

This branch adds a **read-only, manual connection test**, not a live publisher. No Facebook or Instagram posting occurs until official Meta permissions and server deployment are verified.

1. An authorized administrator opens https://developers.facebook.com/apps/ and creates/selects the organization's Meta app. For Facebook Pages request `pages_show_list`, `pages_read_engagement`, and `pages_manage_posts`; for Instagram with Facebook Login request `instagram_basic` and `instagram_content_publish`, with the linked Instagram Professional account. Follow Meta's role/approval process and check app mode/access for the accounts owned by the organization.
2. Verify the authorized Page ID is **61596358055015**, and linked Instagram username is **tlvnet**. Never authorize an alternative page merely because it is accessible.
3. Generate the appropriate Page access token using Meta's authorized login and token exchange flow. Store it exclusively as the GitHub Actions repository secret `TLVNET_META_PAGE_ACCESS_TOKEN` (or, for production, an approved hosted secret manager). Never paste it into chat, a GitHub Issue, a code file, logs, or an automation prompt.
4. Once stored, run **Actions → TLVNET Meta connection check (no publishing) → Run workflow**. Check log output for Facebook Page confirmed and Instagram confirmed. A pass only checks read visibility, not publish capability; do not enable a live schedule based on this test alone.
5. Before enabling publication: deploy a durable publisher with a queue/lock, platform-specific permission test, secure token refresh/re-authorization plan, article/media rights validation, duplicate reconciliation, explicit success IDs, and independent failure alerts. Keep the existing hourly ChatGPT schedule from publishing simultaneously. Test one authorized organic post per platform and verify its permalink.
6. No spending, paid campaigns, credential bypass, or automatic live posting is authorized by this connection test.

Official documentation: https://developers.facebook.com/docs/pages-api/posts/ and https://developers.facebook.com/docs/instagram-platform/content-publishing/ .
