# Bike Closet admission — 3 November 2026 UTC

Big Ring's local configuration gains Bike Closet. The corrected candidate has **19 in-stock listings at least 40% off** above the $1,000 retailer-reference floor. Its 20 discounted products contain 107 variants: 101 confirmed by merchant stock fields and six with unresolved shipping notices. The latter do not qualify for exact-size or stock-only results. Counts are merchant listings, not cross-retailer unique models. Nothing from this follow-up is deployed yet.

## Evidence and corrections

The documented public WooCommerce Store API advertises 31 variable products in Frames And Wheels. A complete traversal checked 26 equipment product pages and their complete variation sets. Five wheel products do not enter the bike/frameset cohort. The scope is this public category's variable products, not the merchant's entire inventory. Full parent IDs, option definitions, exact query destinations, USD minor-unit prices, condition statements and separate stock/backorder flags must agree.

The first attempt failed on typographic apostrophe differences between structured names and API HTML entities; the decoder now normalizes only whitespace and those apostrophes for comparison. Both subsequent full refreshes completed. Existing bounded retries recovered transient HTTP 429 responses; there was no change of identity, network, endpoint scheme or access policy to evade restrictions.

Preview review caught an explicit conflict: TIME Fluidity's title says SIZE L while its sole variant says XS. That offer is excluded, reducing 20 nominal candidates to 19. The final candidate was deterministically filtered from the complete third snapshot, preserving its actual observation timestamp. The raw snapshots remain intact. TIME's manufacturer comes from the explicit Time Frames category, not a guessed title prefix. All 19 separate parent checks confirm the final manufacturer labels.

Shipping notices bind to explicit size/color metadata only when unambiguous. “Rose” matches the single V46 Rose term; missing or multiple matches stay conservative. Older-looking “mid September” notices do not establish arrival. The complete LOOK Huez bike's late-November notice applies to all four sizes. Final-sale terms and Hawaii/Alaska shipping restrictions stay visible. The LOOK Optimum frameset retains a warning that the retailer photo depicts a complete bike. Images use observed medium-resolution sources rather than blurry thumbnails.

An anonymous browser confirmed black/XS on the $799 LOOK Optimum link selects SKU 3611720202321. Blue/XS selects a different SKU; its Store API stock is false, so it is excluded even though the page still renders an Add to Cart control. No cart or checkout action was taken.

## Verification and limits

- All 19 final selected offers matched separately fetched parent and variant endpoints: identity, destination, price, numeric reference, size/options, condition, stock and notices. This audit ran beyond the benchmark's fixed 15-minute window, so it is **source-admission evidence, not a qualified M3 score or population-accuracy claim**. A fresh release audit is required before deployment.
- At 390 × 844, the source-only local preview shows the first complete price at 727.1 px, with no horizontal overflow. Unknown shipping remains readable, and the conflicting L/XS frame is absent. This is not a production performance measurement.
- 546 offline tests pass, including complete/partial header pagination, exact option URLs, currency/minor-unit rejection, shipping scope ambiguity, condition/backorder exclusions, size conflicts, audit mismatches and prior-snapshot retention. Scoped Ruff passes.
- [Source receipt](../../benchmarks/2026-11-03-bikecloset-source.json) and [separate merchant audit](../../benchmarks/2026-11-03-bikecloset-merchant-audit.json) preserve timestamps and limitations. Task-owned public snapshots and the mobile shipping screenshot are under `.local/source-expansion/bikecloset/`.

Retailer reference prices are not proof of former selling prices. No checkout, full landed cost, thirty-day history, production speed gain or all-competitor lead is claimed.
