# Rockler source investigation — 3 November 2026 UTC

## Result

The previously inconclusive search probe is superseded by an observed, working public category feed. Rockler is still **not admitted**. All counts below are discovery candidates, not verified stock or M1 coverage.

The [sale route](https://www.rockler.com/shop-all-deals-power-tools) redirects to the Power Tools category with Clearance, Flash Sale, Sale and Free Gift filters. Its pagination uses `https://rn129l.a.searchspring.io/api/search/category.json` with `siteId=rn129l`, `bgfilter.ss_category=Power Tools`, repeated `filter.ss_morewaystoshop` values and `page`. The ordinary storefront request was observed directly; no authentication, session identifiers or browser cookies were copied into the independent request.

Ten paced public requests traversed the reported terminal page. They returned 223 unique listing IDs against an advertised total of 227. Applying the current tools classifier and $200 reference floor identifies 62 preliminary equipment discounts: 61 simple products and one bundle. Seven have nominal discounts of at least 40%. Exact SKU/package, condition and delivery validation is still required.

## Two admission blockers

1. **Pagination discrepancy.** Page one advertises 24 results but returns 20; the remaining pages return eight sets of 24 and a final 11. No duplicate IDs were found. Merchandising lists two elevated and two removed IDs, but that alone does not explain all four absent records. The documented `resultsFormat=json` reproduces the first-page discrepancy. Do not assume this arithmetic reconciles the catalog, invent missing products, or label the source complete without a documented contract and validation.
2. **Orderability is not stock.** The [Axiom 2X2 CNC router](https://www.rockler.com/axiom-2x2-cnc-router-24-x-24), SKU 77007, is $999 against a $4,699.99 retailer reference. The listing says `in_stock=1`, and the independent product JSON-LD says USD, new condition and InStock. The rendered delivery section instead lists manufacturer shipment estimated for November 14, 2026, with pickup unavailable. Preserve this notice and treat physical stock as unknown. Neither the Add to Cart button nor structured InStock alone resolves the conflict. No cart or checkout action was taken.

The earlier `table saw` text search returned a merchandising redirect to the table-saw category. Its empty results were not evidence of an empty retailer catalog.

## Implementation boundary and acceptance

- Keep source discovery separate from admission until the two blockers are resolved.
- Reuse the shared refresh, exact-offer selection, history and audit machinery. Add only the source-specific category/detail transport and decoding needed by observed Rockler payloads.
- Bind the merchant SKU, canonical destination, selected package, explicit USD price and numeric reference. Handle the bundle separately; do not convert its starting price into an exact purchasable configuration.
- Keep shipping estimates and delivery restrictions on the matching offer. Do not infer physical stock or delivery dates from the generic search index.
- Require deterministic regression fixtures for pagination mismatch, changed totals, duplicate IDs, sale/reference mismatches, option/bundle ambiguity and delayed manufacturer shipments. Use sanitized public product fields, not whole browser pages or request state.
- Compare accepted listings against separate product-page evidence, including all seven deep-discount candidates. Refresh only a new task-owned snapshot during admission. No configured source, existing snapshot, deployment or schedule has changed.

## Evidence

- [Dated discovery receipt](../../benchmarks/2026-11-03-rockler-discovery.json) includes pagination, all seven deep candidates and the sampled product discrepancy.
- Local read-only probe and the full whitelist of 223 returned public records: `.local/source-expansion/rockler/`.
- [Searchspring Category API](https://docs.searchspring.com/reference/get-category), [Search API format contract](https://docs.searchspring.com/reference/get-search), and [merchandising behavior](https://docs.searchspring.com/reference/standard-merchandising). These establish the API semantics; they do not resolve Rockler's observed count mismatch.
