# Rockler source investigation — 3 November 2026 UTC

## Result

The previously inconclusive search probe is superseded by an observed, working public category feed. Rockler is still **not admitted**. All counts below are discovery candidates, not verified stock or M1 coverage. The later investigation below resolves the banner discrepancy and delivery transport, but a live HTTP 429 still prevents admission.

The [sale route](https://www.rockler.com/shop-all-deals-power-tools) redirects to the Power Tools category with Clearance, Flash Sale, Sale and Free Gift filters. Its pagination uses `https://rn129l.a.searchspring.io/api/search/category.json` with `siteId=rn129l`, `bgfilter.ss_category=Power Tools`, repeated `filter.ss_morewaystoshop` values and `page`. The ordinary storefront request was observed directly; no authentication, session identifiers or browser cookies were copied into the independent request.

Ten paced public requests traversed the reported terminal page. They returned 223 unique listing IDs against an advertised total of 227. Applying the current tools classifier and $200 reference floor identifies 62 preliminary equipment discounts: 61 simple products and one bundle. Seven have nominal discounts of at least 40%. Exact SKU/package, condition and delivery validation is still required.

## Two admission blockers

These were the initial findings; see the later resolution and remaining blocker below.

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

## Follow-up: banners, delivery evidence and HTTP 429

The [advanced merchandising contract](https://docs.searchspring.com/reference/advanced-merchandising) explains that inline banners occupy result positions. The observed first page contains four such banners. Setting `disableInlineBanners=true` produces a total of 223 with nine pages of 24 and a final page of seven. Both traversals contain exactly the same 223 product IDs, with no duplicates. The source decoder validates this contract and rejects short pages, banners, inconsistent totals or repeated IDs.

The storefront's public `Forix_SplitCart/js/product/view/delivery-type` component fetches `GET /frx/stockmessage?pid=<product ID>&timezone=UTC`. The product page's delivery component supplies its product ID, SKU and simple-product type. The decoder binds those to the canonical URL, visible name and price, and USD/NewCondition structured offer before fetching delivery evidence. Bundles and grouped configurations remain excluded.

All seven nominal deep candidates have future manufacturer shipment estimates. They retain their active shipping notice and restrictions as unknown-stock offers; generic structured InStock cannot override them. A sampled Bosch jigsaw is explicitly Ready to Ship. Its raw `backorder_date` is also populated, but the storefront displays `estimate_shipping_message`, which is empty for that item. Only explicit ready-to-ship evidence with no active estimate qualifies as confirmed stock. Neither manufacturer shipment nor a freight quote establishes a delivered total price.

The first production-path candidate refresh stopped on HTTP 429 after five product pages and five delivery requests. Existing bounded retries exhausted. No inventory was admitted, no source was enabled, and no live retry followed. Full-price free-gift promotions now skip unnecessary delivery requests after their detail price is checked. Evidence requests stay on the source domain and do not follow redirects. A failed or malformed detail still makes the whole source incomplete and preserves prior successful rows and timestamps.

Local implementation adds the Rockler decoder, opt-in shared delivery fetch and independent-fetch audit support. Full live traversal and a passing audit of the confirmed-stock cohort remain required before catalog configuration changes. The saved discovery and delivery probes do not substitute for those gates. No additional confirmed deep deals or useful retailers are claimed.

See [follow-up admission receipt](../../benchmarks/2026-11-03-rockler-admission.json) for reconciled counts, all eight delivery samples and the failed candidate refresh. Offline verification: 531 tests pass, including 21 Rockler cases; scoped Ruff and diff checks pass. This work is local on `codex/rockler-source`, separate from the pending publication scope for `35f2bfb`.

## November 5 recheck

A bounded feed recheck completed nine banner-free pages with 215 unique products. Current classification identifies 62 preliminary equipment discounts above the $200 reference floor and six nominal deep discounts. All six were already present in the earlier candidate set; SKU 77007 is no longer in this sale traversal. These counts do not establish stock or source admission.

The first exact detail check stopped on an identity contradiction: the Axiom AR8 Elite page has the expected title and heading, but its canonical destination points to an unrelated Kutzall rotary-tool accessory. The existing decoder correctly rejects it. No delivery request or retry followed, and the other five deep candidates were not checked. November 3 shipping observations remain dated evidence. Rockler stays inactive; no parser or production configuration changed. See [recheck receipt](../../benchmarks/2026-11-05-rockler-recheck.json).
