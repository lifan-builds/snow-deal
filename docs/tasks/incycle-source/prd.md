# Incycle complete-bike source

Status: in progress under existing source-expansion authorization; source remains inactive until complete candidate and merchant audit pass.

Recover high-value bicycle discounts from Incycle using the existing Shopify ingestion and exact-variant machinery. The public sale-bicycles feed has 87 products, all under generic Sporting Goods taxonomy. Existing classification accepts 19 framesets and rejects 67 parsed complete-bike candidates. Primary research found 13 available selected offers at least 40% off with retailer references above USD 1,000; eight are currently rejected by classification. These are research candidates, not admitted inventory.

Accept only explicit observed complete-bike taxonomy on Incycle's exact host. Keep generic Sporting Goods alone rejected. Preserve accessory, child/condition, shipping, frameset and exact-size gates, and all other sources' behavior. Do not guess a Large size from a title for a Default Title variant. Percentage-off ranking and historic-price disclosures remain unchanged.

Require bounded full source traversal, declaredUSD verification, fixed top 10 / seeded 20 plus every deep selected listing merchant audit, separate product fulfillment checks, full tests/review, history-preserving preview/production rollout and live receipts. Standing comparable-release approval applies; no account changes or purchases.
