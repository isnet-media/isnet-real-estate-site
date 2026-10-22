# Rishon LeZion supermarket operations

Canonical site: https://isnet.co.il/SUPER.RISHON/ . Independent data and browser shopping lists; the shared visual components are retained.

## Sources reviewed 22 October 2026

24 physical branches, 11 chains. Each accepted branch has its official chain/store XML identity and a price file dated 22 October. Public branch directory plus the official Stores file verify Keshet 013 at Barshavsky 33; the directory classifies this customer-facing branch despite the source Stores type code 3.

Carrefour 405 remains pending: the filename declares 405 but the embedded StoreID is 114. Do not override the identity check. Keshet 024 at Lehi 4 remains pending because no full price file was received. Neither receives invented observations or participates in the connected-branch ranking. Source status displays both pending branches. Tiv Taam collection-only 514 is excluded.

The existing chain feed connectors are reused by `refresh_rishon_super_prices.py`, with an isolated RISHON data root. No Ashdod, Yavne or Kiryat Gat schedule is changed. Daily refresh: 06:15 UTC. Failed connected branches retain their previous data and file dates; the report records each result. Missing promotions are not fabricated. Data is committed only after the builder and publication tests pass. Pages listens to successful completion and rebuilds before deployment. Evidence is retained for 30 days.

## Fixed basket

16 reviewed lines cover all 24 connected branches. The family selection is independent of other cities. Frozen salmon totals exactly 3 kg: 5 x 600 g, 6 x 500 g or explicit kg offers. Cottage is 5% / 250 g; oil is regular canola / 1 litre; salt is table salt / 1 kg. Fixed candidate order, whole package counts, no inferred prices or units. Other lines use the same barcodes. The basket contains dairy, frozen fish, canned vegetables and pantry products; no fresh meat, poultry, fruit or vegetables. These remain searchable in the product comparison where published.

600–700 ILS is an editorial target, not a forced result: the first genuine city mean is 722.05 ILS (range 601.90–854.18). Do not adjust quantities on refresh to force that target. The basic 12-barcode basket can be incomplete and must clearly identify missing products; it is not the default family comparison.

Recipe costs retain the explicitly labelled Ashdod reference from 21 October; they are not represented as current Rishon ingredient prices. No analytics tag from another city is copied.

## Checks and rollout

`build_rishon_super.py` builds baskets, smart brand alternatives and the shared header across all current/new HTML. `test_rishon_super.py` verifies city isolation, branch references, fixed full basket sums and kg quantities, finite prices, logos, and local links/assets. Check public prices, refresh status and family basket after publication. Three complete daily collections on separate dates are needed before claiming stable daily collection. A rebuild does not count as another scan. Retailer price files do not guarantee stock or checkout pricing.
