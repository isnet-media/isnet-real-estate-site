# Yavne supermarket edition
Canonical URL: https://isnet.co.il/SUPER.YAVNE/ . Uses the existing shared ISNET Pages deployment and supermarket frontend. Ashdod data and schedules remain independent.

Seven reviewed physical Yavne branches: Rami Levi 040; Freshmarket/Mahsaney Lahav 025; Carrefour 124 and 125; Shufersal 122 and 779; Victory 056. Identity sources are recorded in catalog.json. The branch in Gan Yavne is NOT Victory 056. No nearby-city branches are substituted.

Refresh Yavne supermarket prices runs daily at 05:35 UTC and on demand. It reuses refresh_super_prices.py official-feed adapters through super_city_runtime.py, scoped to SUPER.YAVNE/data. Existing verified branch product counts provide the collector's count bounds. Adding a branch requires identity review and a separately verified initial snapshot, never a guessed count. Failed downloads retain the last verified source date and prices. Status is public in data/refresh-status.json. Pending independent local shops have no invented prices.

build_yavne_super.py reuses the existing fixed basket, smart shopping and shared shell. The only new family-basket equivalent is reviewed Medjool dates barcode 7296073706229: 5 whole 400g packs = the same 2kg. All original quantities remain unchanged. The family basket must include all connected branches. Daily refresh candidate checks run before committing only Yavne data. No rollback of Ashdod data, no duplicated Ashdod collector and no shared shopping-list key.

Public recipe estimates remain the dated Ashdod reference from 21 October, labelled on recipe pages. They are not claimed to be current Yavne branch costs. No Ashdod GA4 tag is copied to Yavne. Initial connected-scope completeness is not a claim of every shop in the city or three consecutive successful daily collections.

Local shop candidates supplied by the publisher are recorded separately in source-status.json. Malls, restaurants and unverified fictional listings are not connected supermarkets. Source availability is not an inventory guarantee.
