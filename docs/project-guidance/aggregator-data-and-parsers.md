# Aggregator data and parser contracts

## Parser pipeline

All I/O is async. New static parsers inherit `deal_common.parsers.base.BaseParser` and import shared `parse_price()` from `common/deal_common/parsers/common.py`; do not create parser-local copies. Browser extractors remain `(wait_selector, js_extract, next_page_selector)` entries, use `forEach` for NodeLists, and prefer `domcontentloaded` for anti-bot sites.

Every product path must preserve `image_url`, price, category, brand, and size/length behavior. Image extraction uses Shopify `images[0].src` or browser `data-src || src`. Price parsing must accept decimal and whole-dollar comma prices.

Ski Essentials Show More can be covered by its newsletter dialog. Dismiss only the observed `POPUP Form` close control on that retailer; keep the increasing-product-count wait and pagination-error reporting. An accepted click alone is not traversal proof. Cumulative listing DOM counts are not unique product counts.

## Data-quality invariants

1. Test categorization before scraping; miscategorized products pollute durable snapshots.
2. Space-pad exclusion terms and prepend a space to the normalized name/URL before matching.
3. Put ambiguous model names in brand-qualified multi-word mappings.
4. Apply exclusion guards before brand fallback.
5. Preserve the layered boot disambiguation pipeline.
6. Strip store domains before category matching.
7. Use per-domain concurrency limits.

Review matching is precomputed into `deal_reviews` after review ingestion. `query_deals()` left-joins those rows; never restore per-request fuzzy matching. `_extract_brand()` is shared by scraping and reviews. SQLite latest-per-store queries use grouped joins rather than correlated O(N²) subqueries.

Never run a live scrape, review fetch, browser session, auth sync, invite generation, or production database operation as generic migration validation.


## Cycling and tools catalogs

- `Catalog.size_option_names` opts a Shopify catalog into explicit dimension names. Cycling accepts frame/bike size, not wheel size; missing option metadata stays unknown. Default snow size/length discovery is unchanged.
- Cycling also supplies `Catalog.size_value_pattern`: a Size label alone is insufficient when a merchant swaps Size and Color metadata. Keep unrecognized values in raw options but withhold them from exact-fit fields; never infer a replacement from a Color option. Snow and tools retain their existing behavior unless explicitly opted in.
- Snow's `exclusion_reason` is shared by ingestion and downloaded-snapshot repair. Explicit blem/blemished evidence is excluded from the normal-condition cohort without rewriting price or freshness history. A standalone Demo word can describe an adjustable binding design and is not sufficient evidence of prior use.
- A Shopify offer destination must stay on its product path and carry exactly the matching `variant` query ID. Grizzly's single-SKU product pages instead require the configured Grizzly parser, an exact SKU/path-suffix match, identical product/offer URLs, explicit USD price and strikethrough reference, and new/in-stock evidence. Never invent a Shopify variant query for a SKU page or relax Shopify validation for other sources.
- Variant history matches source, product URL/name/brand and variant ID/options/destination. Ingestion and history share the exact manufacturer-label cleanup: fulfillment labels are unknown manufacturers, so cleaning them must not hide an otherwise identical observation. Real manufacturer changes still break identity. Normalize only for comparison; never rewrite historical price, stock, reference or timestamps. Count distinct UTC observation dates; incomplete refreshes do not create observations. Catalog currency is fixed to USD. Package builds must preserve the last 45 days of configured-source observations.
- Competitive evidence lives in `docs/COMPETITIVE-BENCHMARK.md` and dated `docs/benchmarks/` records. Unmeasured, provider-claimed or incomparable values cannot justify a market-leading claim.
- Retailer taxonomy such as Bike Lock, Bike Pumps, Bike Part and Bike Maintenance identifies accessories even though it contains Bike. Cable lengths and tire-width dimensions cannot satisfy a frame-size request. Fulfillment messages in a vendor field are not manufacturer or stock evidence; retain unknown manufacturer status rather than inventing a brand.

## Catalog freshness, observations and merchant audits

Current browsing expires source observations after 24 hours; future timestamps are invalid. Failed refresh attempts cannot renew freshness. Catalog history retains the latest successful observation per UTC date for 45 days. Restore the previous public catalog snapshot before refresh; only an explicitly approved first-run bootstrap may start without an asset. Download errors are never bootstrap permission.

Catalog definitions may provide explicit manufacturer aliases; common normalization applies only those mappings. Do not fuzzy-merge model identities or assume package compatibility. Merchant auditing uses a separate public product endpoint and exact selected variant, records unresolved responses, and stops a host on HTTP 403/429. A declared MSRP/retail-price metadata option is not a size/color option; retain its evidence while comparing actual purchasable dimensions. Endpoint agreement is not checkout validation or proof of historical street price.

## Source expansion receipts

Use `scripts/probe_sources.py` with an explicit public candidate manifest and a new output directory. This invokes the production refresh/classification/query path, records complete versus partial collection outcomes, and never enables a retailer automatically. Candidate snapshots are task-owned public data, not operational databases. Preserve their actual observation timestamps when importing accepted sources into a preview; do not refresh old sources merely to add new ones.

Retain Shopify tags for catalog eligibility, including observed shipping-only or condition restrictions. Retailer taxonomy is evidence: Hardtail/Full Suspension are bike types; cutters, knives, stands, and books are not powered machines. A contradictory title such as Recon overrides a structured NewCondition claim. Grizzly pagination must report the requested page and a terminal page; the catalog CLI has a bounded 30-page budget, and reaching it early is an incomplete refresh. Merchant samples use the separate exact-SKU product page for Grizzly. HTTP 403/429 remains unresolved evidence, never an accuracy pass.

Shipping restrictions take precedence over positive shipping tags. Fanatik can mark the same product `ship-usa` and `in-store-only`/`no-ship`; its condition tags can also disclose open-box, lightly ridden or cosmetic-blemish stock absent from the title. Inspect the separate product page as well as price/variant JSON before admitting a source. A price audit match does not prove shipping eligibility. Keep showroom machines out of the new/shippable tools catalog. Match specific accessory taxonomy without rejecting actual jig saws, fat-tire bikes or machines with digital displays. Proprietary model taxonomy (such as State's `6061 All Road`) requires observed brand and bicycle-tag evidence. Frame-size aliases SM/MD/LG may match S/M/L, but compound sizes must remain intact.

## Harvey shipping evidence

Harvey's vendor-field `ESD:` notice is shipping evidence, even when Shopify reports `available: true`. Preserve the notice on affected offers and withhold confirmed-stock status. Bind a parenthesized color qualifier only through explicit Color/Colour metadata and a matching variant; ambiguous scope applies conservatively to all variants. Never infer arrival from an old-looking date or invent a year. The independent product audit uses the same notice decoder on its separately fetched payload and rejects a delayed variant as confirmed stock. Carry the notice through current cards and dated history; older observations without the field remain readable and are not rewritten.

## Taylor detail-page contract

Taylor's parent listing IDs differ from its purchasable SKU identities. `TaylorParser` decodes the page's JSON literal assignments without executing merchant JavaScript, checks canonical product identity and the explicit US-price container, and binds the selector SKU to its complete option query. Both single- and multi-SKU links were verified in an anonymous browser. Missing stock, backorders, factory-second levels, malformed prices and ambiguous option destinations cannot become offers. Detail breadcrumbs supply the authoritative category; listing names are only a request-saving prefilter.

Taylor's normal pagination is cumulative. Validate the requested page, page size, advertised total and unique listing IDs. Different listing IDs may alias one product URL; fetch that canonical detail only once. Show All must still match the advertised total and the bounded listing cap. Shared HTTP detail resolution is opt-in, paced, bounded and source-domain restricted. Any failed or malformed detail makes the entire source incomplete, preserving previous successful rows and observation timestamps. Keep prior Shopify/Grizzly validation intact.
