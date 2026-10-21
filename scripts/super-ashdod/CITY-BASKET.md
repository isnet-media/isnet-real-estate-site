# Fixed city basket

Main site feature: immediately after the category rows, at the beginning of the home view.

Default family comparison: 22 lines, including whole fresh chicken, packaged frozen salmon, fruit, vegetables, canned legumes/corn, bread, dairy and pantry items. Quantities are an editorial shopping example aimed at a roughly600–700 ILS mean, not a measured average household budget or nutritional plan. Actual prices are never changed to fit the target. The UI shows the actual mean and compares only complete branch baskets. The basic12-product variant initially has identical GTIN coverage at all14 ingested branches.

Packaged goods use identical GTINs and whole package counts. Fresh items use an explicitly curated list of equivalent kind/variety with fixed kg quantities; producer, kosher certification, size and quality may vary. The exact selected code is retained for every branch. Candidate order is fixed, never cheapest-price selection. Both product metadata and offer raw units must indicate kg and the raw and normalized prices must agree. Malformed weighted metadata is excluded. No estimated replacements, mixing shops, promotions or zero filling.

Sources: data/catalog.json plus data/offers/*.json and source-status.json. Source file date and product price-change date are separate. Stock is not guaranteed. Shufersal and other unconnected chains are disclosed. All winning/highest ties are retained. Percentage difference uses the cheapest full basket as denominator.

Definitions: city-family-basket.json and city-basket-products.json in this directory.
Rebuild: python scripts/build_super_city_basket.py
Verify: python scripts/test_super_city_basket.py
The publishing workflow rebuilds from the latest ingested catalog before deployment.

## Comparable items
Family basket candidate priority is stable: reference product first, then explicitly approved equivalents. Bread alternatives retain 750 g whole-wheat packages and package counts. Frozen salmon alternatives retain frozen fillets/portions and 1.8 kg total; skin/cut/brand differences are disclosed. Weighted alternatives require explicit kg metadata on both product and offer with unchanged raw price. Each line exposes `match_type`, actual product ID/name, actual purchased quantity, pricing unit and any equivalence note; branches expose `equivalent_count`. No cross-branch price imputation or zero-filling. A missing offer is not a claim that the store does not sell the item. Invalid or ambiguous weight data remains excluded.
