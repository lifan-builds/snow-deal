# Source expansion — November 2026

Four retailers were selected after checking public storefronts, collection feeds, available variants, prices, product destinations and market currencies. The initial full local check completed all 14 collections (16 feed pages), returning 394 discounted listings with no collection errors.

| Retailer | Scope | Price market | Initial listings |
| --- | --- | --- | ---: |
| [UtahSkis](https://utahskis.com/collections/sale) | Skis, snowboards, boots and bindings; six collections | USD | 126 |
| [The Startingate](https://shopstartingate.com/collections/sale-items) | Skis, ski boots and bindings; three collections | USD | 77 |
| [Freeride Boardshop](https://www.freerideboardshop.com/en-us/collections/sale-snowboards) | Snowboards, boots and bindings; three collections | USD, explicit US market | 45 |
| [Boardom](https://boardom.net/collections/clearance-snow?currency=CAD) | Ski and snowboard clearance; two collections | CAD, explicit currency selection | 146 |

The Startingate's standalone bindings feed was valid but had no qualifying discounted offers. Its broader sale collection includes fashion footwear, so only the reviewed snow-sport collections are enabled. None of the new sources is labeled tax-free.

## Price and metadata safeguards

Boardom's default market returned USD; Freeride redirected to its US market. Every new collection must expose the expected Shopify currency before its prices are accepted. Missing, malformed or mismatched currency evidence is reported as a failed collection. Locale paths and explicit currency selections survive feed pagination and product links. Returned deals also carry the configured currency before persistence.

Real feed samples exposed three parser defects: `NA` was treated as an available size, wide snowboard lengths such as `161W` were omitted, and the `R22` ski interface matched the clothing keyword `R2`. These are corrected with regression fixtures. Fractional lengths remain unrounded. Missing retailer images and sizes remain unknown rather than invented.

## Candidates held back

- [Gravity Coalition](https://gravitycoalition.com/collections/powder-ski-sale): feeds combine different models, model years and bundles under one product. A variant-aware identity adapter is needed before prices can be compared accurately.
- [Next Adventure](https://nextadventure.net/collections/ski-snowboard-up-to-60-off): storefront distinguishes online and in-store stock, but the generic feed does not reliably expose that distinction. Avoid presenting pickup-only offers as online inventory.
- [Boyne Country Sports](https://boynecountrysports.com/collections/sale-skis): storefront responds, but the conventional collection JSON endpoint does not. Needs a supported feed or dedicated adapter.
- Powder7 remains a candidate for a new-only inventory adapter; its used-gear coverage should not enter new-product comparisons without condition handling.

Existing unresolved connections remain visible: MEC is blocked by verification, and Ski Essentials has partial pagination. This expansion does not claim to repair those connections.

## Verification

145 offline tests passed, including public feed excerpts from all four retailers, market-preserving pagination and destinations, fail-closed currency checks, available-price/size handling, child-product exclusion and the metadata edge cases above. Python compilation and whitespace checks passed. The production refresh is scoped to these four retailers to preserve other retailers and existing price history.

## Verified production result

[Run 41362079607](https://github.com/lifan-builds/snow-deal/actions/runs/41362079607) succeeded on revision `e5e6da5`. Production `/healthz` independently returned the exact snapshot timestamp `2026-11-01T23:28:08.392435`, with 30 retailers holding current listings. The store report showed 13,969 listings and 29/31 complete recent checks; all four new retailers were marked OK with the counts above.

All 14 new collections completed without errors, publishing 394 deals. They have zero missing categories, three missing images, 11 missing sizes and 12 missing lengths among 146 skis/snowboards. The remaining missing values are not fabricated. The public snapshot passed SQLite integrity checks and price/currency/link assertions. All 14,036 preexisting deal rows were unchanged, and all 42,338 prior price observations survived; history now contains 42,732 observations.

Live retailer-filter responses returned only the selected retailer, showed USD for UtahSkis, The Startingate and Freeride, and CAD for Boardom. Freeride's US-market product paths and Boardom's CAD query selection were preserved in rendered deal links. These sources are included in the existing daily refresh schedule.
