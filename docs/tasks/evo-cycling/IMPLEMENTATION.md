# evo cycling source admission — 3 November 2026 UTC

The earlier zero-admission result was caused by a category gap, not an empty sale inventory. A complete public bikes-feed traversal returned 493 unique products in two pages. The existing Shopify decoder found 70 discounted products with available variants, all rejected by the old cycling classifier because evo uses explicit `Completes` taxonomy and year-suffixed titles.

Recognizing the three observed taxonomy values and excluding `badge:Ship to Store Only` yields **55 eligible listings, including three at least 40% off**, at the $1,000 retailer-reference floor. Fourteen discounted products carry the store-only restriction, including one also tagged Free Bike Ship. One other product is explicitly blemished. Neither is admitted. Stock-false variants remain excluded; price, reference, size, color and purchase URL remain attached to the same variant.

Fresh production-path admission completed at 17:13 UTC with USD verified. The separate top-ten plus seeded-twenty merchant audit matched **30/30** in 163 seconds, with no mismatch or inconclusive result. The new audit timing gate records completion times. This is endpoint agreement, not proof of 99% population accuracy, checkout completion or historical selling prices.

Anonymous browser checks of all three deep listings confirmed their selected variants and displayed inventory: Mondraker RAZE R XL ($2,500.09 / $4,999), Devinci Chainsaw XL ($2,220.10 / $3,699), and Santa Cruz 5010 XXL ($6,179.40 / $10,649). The Mondraker shipping details state a flat rate at checkout, contiguous-US restrictions and 2–4 assembly days before shipment. Free shipping applies to ship-to-store; Big Ring does not promise free home delivery. A separate Transition Sentinel check displayed ship-to-store-only terms and corroborated its exclusion despite the positive shipping tag.

Nine deterministic regressions cover category/variant preservation, shipping precedence, blemished/used exclusions and unrecognized/accessory taxonomy. All 559 offline tests pass. The existing shared refresh, normalization, query and merchant audit are reused; no new adapter or snow-parser change was needed.

Evidence: [source receipt](../../benchmarks/2026-11-03-evo-cycling-source.json) and [merchant audit](../../benchmarks/2026-11-03-evo-cycling-merchant-audit.json). Task-owned public snapshots remain under `.local/source-expansion/evo-review/`. Prior saturation evidence remains historical and is not overwritten.

## Rollout

This branch follows PRs #8 and #9; their release refs stay unchanged. After their rollout is verified, require CI and merge under the user's standing authorization, then run the existing fresh catalog workflow with history restoration. Require all configured sources, merchant checks and exact live hashes. Keep the current live snapshot if admission fails. No new account, credentials, paid plan or DNS change is involved. This source improves coverage; all-competitor leadership remains unproven.
