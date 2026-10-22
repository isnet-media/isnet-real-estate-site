# Kiryat Gat supermarket edition

Canonical URL: https://isnet.co.il/SUPER.KGAT/ . Shared ISNET Pages hosting and mobile supermarket interface; independent city data and shopping-list key isnetKgatBasket. Ashdod and Yavne collection scopes and schedules are unchanged.

## Connected physical branches

Reviewed on 22 October 2026 using retailer Stores XML or the retailer's current branch selector:

| Chain | Store | Identity/address |
| --- | --- | --- |
| Rami Levi | 054 | Big, Derech Hadarom 3 |
| Rami Levi | 061 | Karmi Gat; exact street not established by the reviewed source |
| Shufersal/Universe | 214 | Malchei Israel 178 |
| Shufersal Deal | 254 | Karmi Gat, Avnei Hoshen 1 (publisher supplied address) |
| Shufersal Express | 743 | Hagvura 28 (directory address; selector verifies city/store identity) |
| Victory | 055 | Hagefen 3 |
| Netto Chisachon/Sapir | 191 | Esther Hamalka 19 |
| Shuk Hair | 009 | Derech Hadarom 13 |
| Machsaney Hashuk | 077 | Official Stores says Derech Hadarom 1; publisher list says 2. Address discrepancy recorded, not silently resolved. |

Official source URLs, identity file names, price-file dates and XML SHA-256 fingerprints are recorded per branch in catalog.json and refresh-status.json. The initial snapshot has 31,278 unique products and 78,655 branch offers, all with source publication dates 22 October 2026. Product price-change dates can be earlier; published price data does not establish stock.

## Collection and publication

Refresh Kiryat Gat supermarket prices runs at 05:55 UTC, daily and on demand. scripts/refresh_kgat_super_prices.py uses the shared collector with a city-scoped module; Bina feeds use the observed all-file endpoint (including promotions), and Machsaney Hashuk uses its official Laib feed. XML chain/store identity, full-file plus ordered deltas, freshness, rollback and product-count checks apply before atomic branch replacement. Existing verified product counts establish count limits. New stores require an independently reviewed bootstrap snapshot, never a guessed count.

Failures preserve the previous verified branch data and its date. data/refresh-status.json exposes per-source results, and coverage_complete is false if any source was retained. Validations run before committing only SUPER.KGAT/data. Publish priceboard rebuilds the city basket, smart-shopping groups and shared shell and verifies local links, city isolation, arithmetic and JavaScript syntax. No extra Ashdod collector is created.

## Fixed basket and presentation

The city-specific family basket has 16 lines with full price coverage in all nine connected branches. It contains 12 litres milk, 8 cottage-cheese tubs, 4 kg rice, 4 pasta packs, other pantry goods, wholemeal bread, 1.8 kg frozen salmon, 1.2 kg frozen peas, 1.6 kg frozen peas/carrots and 2 kg fresh bananas. Bananas replace packaged Medjool dates because dates with equal total quantity could not be verified at Netto Chisachon. Reviewed alternatives for Shufersal peas/carrots and Machsaney Hashuk ptitim, table salt and classic instant coffee are explicit in scripts/super-kgat/city-family-basket.json. Priority is fixed, not cheapest-product cherry-picking. Weighted bananas require explicit kg fields in product and offer. The mean at launch is NIS 634.70; the NIS 600–700 target is the average, not a fabricated branch total. The separate basic basket can be partial and is labelled accordingly.

Recipe estimates remain a dated Ashdod reference from 21 October, explicitly labelled on recipe pages, not purported current Kiryat Gat prices. No Ashdod analytics ID is copied to this edition.

## Unconnected candidates

source-status.json lists publisher-supplied local shops separately. City Market official portal lists Karmi Gat store 070, Lachish 181, but filters for 20–22 October returned no full price files. It is not counted as connected. The second City Market at Lachish 37 was not found in that selector. Gat Market, Flamingo, Birkat Chaim, Kiri Market, Mix and Neve Hai await a verified direct price source. Malls, the restaurant and pharmacy are not grocery branches. The old Carrefour listing at Esther Hamalka 19 is not double-counted with current official Sapir store 191; no closure is inferred.

Official Stores feeds checked for Yohananof, Osher Ad, Tiv Taam, Keshet, Freshmarket and Carrefour contained no reviewed physical Kiryat Gat branch. Gan Yavne, Kiryat Malachi and other nearby towns are not substituted. Initial successful collection is not three successful daily collections or complete coverage of every local shop.
