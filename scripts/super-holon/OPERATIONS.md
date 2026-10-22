# Holon supermarket operations

Canonical public URL: https://isnet.co.il/SUPER.HOLON/ . Branding: מחירי הסופר בחולון, מבית חולון נט. Source data, shopping lists and routes are isolated from all other cities.

## Reviewed sources — 22 October 2026

23 physical branches in 11 chains: Rami Levy 050/718; Yohananof 073; Tiv Taam 020/079; Freshmarket/Super Dosh 039; Victory 039/060; Carrefour 067/329/345; Shufersal 018/082/123/247/265/318; Super Sapir 160/190; Shuk Hair 014; Super Bareket 062; Hazi Hinam 202/204. Official Stores identities, city code 6600 (or explicit Holon name), and embedded price-file chain/store identities were checked. Yohananof's address is filled from the reviewed physical-branch address because its Stores address is `unknown`. The branch registry preserves original Stores evidence hashes.

Bareket Stores type 3 at Landau 16 is accepted because its official accessibility directory independently confirms the customer-facing branch. Freshmarket 023 at HaLohamim 1 is excluded pending resolution of conflicting official city/address evidence. Shufersal 631 duplicates 318's address; BE 270 is a pharmacy. Super Sapir Wolt 130/150 duplicate physical stores 190/160 and are excluded. Hazi Hinam delivery 103 and produce department 217 are not counted as additional physical supermarkets; department 217's separate observations are not imported into 204. City Market and Super Yuda remain pending, without invented price observations. Pending discovery does not invalidate a complete refresh of the registered cohort.

Connectors: shared PublishedPrices, Carrefour, Shufersal and Laib connectors; isolated Bina adapters for Sapir, Bareket and Shuk Hair; Hazi Hinam's own public `/Prices` HTML table with bounded pagination and allowlisted official Azure downloads. Never substitute its delivery store for a physical branch. Every downloaded price XML passes chain/store identity, finite-price, count, timestamp and rollback checks. Initial bootstrap count allowance was applied only in an ephemeral bootstrap runtime, never to the recurring collector. Subsequent updates retain the established count guards.

Daily collection: 06:45 UTC, separate workflow `Refresh Holon supermarket prices`. Run refresh, build and tests before committing only Holon data. No other city's schedule is changed. Failed connected sources retain their previous snapshot and original dates. Keep refresh evidence for 30 days. Pages listens for successful workflow completion, rebuilds and verifies before publishing. Rebuilds are not scans. Three complete successful daily scans on separate dates, followed by public verification, are required before declaring stable recurring collection.

## Fixed basket

16 family lines cover all 23 connected branches. Initial genuine mean: 634.00 ILS; minimum 549.60; maximum 709.68. Fixed quantities include 12 litres of milk; 6 x 250 g cottage; 4 x 250 g white cheese; rice, pasta, ptitim, canola oil, salt, coffee, crackers, mayonnaise, canned tomatoes; 2 x 600 g peas; 2 x 600 g green beans; 4 x 700 g prepared chicken schnitzel (2.8 kg). This is a defined comparison basket, not a full nutritional meal plan or a statistical measure of family spending. It contains prepared chicken, not raw meat or fish. Those products can be compared separately in product search. Only canola oil uses reviewed equivalent 1-litre products, in fixed priority; other family lines use identical barcodes and whole packs. Do not change quantities on refresh to force a 600–700 ILS result.

The optional 12-barcode basic basket is partial (13/23 initially), explicitly labelled, and never the default. Missing prices are never zero or imputed. Promotions are not applied to basket totals. The 309 initial selected promotions span all 11 connected chains; only simple, current, quantity-one, unrestricted specials with verified savings are shown. Published price files do not guarantee stock or checkout pricing.

18 smart-shopping categories use 211 reviewed products across 23 branches, retaining exact type and package-size rules. Recipe estimates explicitly retain the Ashdod reference dated 21 October, not current Holon ingredient costs. No analytics identifier from another city is copied.

## Verification

`build_holon_super.py` builds city baskets, alternatives, current intro counts and the shared header. `test_holon_super.py` checks city isolation, finite offers, branch references, basket sums, chicken/vegetable quantities, logos, browser list namespace and public links. JavaScript syntax checks cover every city script. Mobile browser QA covers home, grouped product results, all branch prices and list add/remove. Verify the canonical URL and public prices, refresh status and basket after deployment.
