# Incycle complete-bike source

Status: released and verified in PR #36 on November 5, 2026. Source admission, final audit, CI, history preservation and production checks passed; see `docs/benchmarks/2026-11-05-incycle-rollout.json`.

The task recovered high-value bicycle discounts from Incycle using the existing Shopify ingestion and exact-variant machinery. At discovery, the public sale-bicycles feed contained 87 products, all under generic Sporting Goods taxonomy. The prior classifier accepted 19 framesets and rejected 67 parsed complete-bike candidates. Initial primary research found 13 available selected offers at least 40% off with retailer references above USD 1,000; eight were omitted by that classifier. Those figures describe the research baseline; the dated rollout receipt records the admitted production inventory.

Accept only explicit observed complete-bike taxonomy on Incycle's exact host. Keep generic Sporting Goods alone rejected. Preserve accessory, child/condition, shipping, frameset and exact-size gates, and all other sources' behavior. Do not guess a Large size from a title for a Default Title variant. Percentage-off ranking and historic-price disclosures remain unchanged.

Require bounded full source traversal, declaredUSD verification, fixed top 10 / seeded 20 plus every deep selected listing merchant audit, separate product fulfillment checks, full tests/review, history-preserving preview/production rollout and live receipts. Standing comparable-release approval applies; no account changes or purchases.
