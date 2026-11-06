# Aggregator data and parser contracts

## Parser pipeline

All I/O is async. New static parsers inherit `deal_common.parsers.base.BaseParser` and import shared `parse_price()` from `common/deal_common/parsers/common.py`; do not create parser-local copies. Browser extractors remain `(wait_selector, js_extract, next_page_selector)` entries, use `forEach` for NodeLists, and prefer `domcontentloaded` for anti-bot sites.

Every product path must preserve `image_url`, price, category, brand, and size/length behavior. Image extraction uses Shopify `images[0].src` or browser `data-src || src`. Price parsing must accept decimal and whole-dollar comma prices.

Ski Essentials Show More can be covered by its newsletter dialog. Dismiss only the observed `POPUP Form` close control on that retailer; keep the increasing-product-count wait and pagination-error reporting. An accepted click alone is not traversal proof. Cumulative listing DOM counts are not unique product counts.

## Data-quality invariants

Percentage eligibility and ordering use `deal_common.offers.discount` on the selected variant's decimal prices. Round only in presentation. Snow registers this same calculation as `price_discount` on list and count connections so old cached rounded percentages cannot change thresholds, variant choice or pagination. Legacy product rows also derive their percentage from prices; this read-time correction never rewrites snapshots or history.

Selected snow offers carry the database's `variant_key` into `AggregatedDeal` alongside options, price and purchase URL. The disclosure must show that same identity; legacy rows keep `None` and the unknown-variant notice. Do not reconstruct a selected key from a URL or change stored history.

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

Cycling's generic Bike taxonomy cannot override an apparel primary title. Separate an explicit included-accessory suffix (`with`, `w/`, `including`) before checking apparel identity, while retaining full-title condition restrictions and negative retailer taxonomy. A complete bicycle with gloves or a rack stays a bicycle; gloves with a bicycle mentioned later do not. Explicit bicycle-frame taxonomy uses a full match, including singular/plural mountain, road, gravel and other observed frame types, before complete-bike fallback. A carbon-frame description alone does not make a complete bicycle a frameset. Preserve raw merchant names and exact offer fields even when correcting the category; verify package evidence on ambiguous product pages before release.

## Catalog freshness, observations and merchant audits

Current browsing expires source observations after 24 hours; future timestamps are invalid. Failed refresh attempts cannot renew freshness. Catalog history retains the latest successful observation per UTC date for 45 days. Restore the previous public catalog snapshot before refresh; only an explicitly approved first-run bootstrap may start without an asset. Download errors are never bootstrap permission.

Catalog definitions may provide explicit manufacturer aliases; common normalization applies only those mappings. Do not fuzzy-merge model identities or assume package compatibility. Merchant auditing uses a separate public product endpoint and exact selected variant, records unresolved responses, and stops a host on HTTP 403/429. A declared MSRP/retail-price metadata option is not a size/color option; retain its evidence while comparing actual purchasable dimensions. Endpoint agreement is not checkout validation or proof of historical street price.

## Source expansion receipts

Use `scripts/probe_sources.py` with an explicit public candidate manifest and a new output directory. This invokes the production refresh/classification/query path, records complete versus partial collection outcomes, and never enables a retailer automatically. Candidate snapshots are task-owned public data, not operational databases. Preserve their actual observation timestamps when importing accepted sources into a preview; do not refresh old sources merely to add new ones.

Retain Shopify tags for catalog eligibility, including observed shipping-only or condition restrictions. Retailer taxonomy is evidence: Hardtail/Full Suspension are bike types; cutters, knives, stands, and books are not powered machines. A contradictory title such as Recon overrides a structured NewCondition claim. Grizzly pagination must report the requested page and a terminal page; the catalog CLI has a bounded 30-page budget, and reaching it early is an incomplete refresh. Merchant samples use the separate exact-SKU product page for Grizzly. HTTP 403/429 remains unresolved evidence, never an accuracy pass.

Shipping restrictions take precedence over positive shipping tags. Fanatik can mark the same product `ship-usa` and `in-store-only`/`no-ship`; its condition tags can also disclose open-box, lightly ridden or cosmetic-blemish stock absent from the title. Inspect the separate product page as well as price/variant JSON before admitting a source. A price audit match does not prove shipping eligibility. Keep showroom machines out of the new/shippable tools catalog. Match specific accessory taxonomy without rejecting actual jig saws, fat-tire bikes or machines with digital displays. Proprietary model taxonomy (such as State's `6061 All Road`) requires observed brand and bicycle-tag evidence. Frame-size aliases SM/MD/LG may match S/M/L, but compound sizes must remain intact.

evo's `Mountain Completes`, `e-Mountain Completes` and `Gravel Completes` are explicit complete-bike categories. Do not require these products' year-suffixed names to end in Bike, and do not broadly accept arbitrary `Completes` labels. Its `badge:Ship to Store Only` restriction overrides `Free Bike Ship`. That positive tag alone does not promise free home delivery: observed bike shipping details distinguish a checkout flat rate from free ship-to-store and state geographic/assembly restrictions.

## Harvey shipping evidence

Harvey's vendor-field `ESD:` notice is shipping evidence, even when Shopify reports `available: true`. Preserve the notice on affected offers and withhold confirmed-stock status. Bind a parenthesized color qualifier only through explicit Color/Colour metadata and a matching variant; ambiguous scope applies conservatively to all variants. Never infer arrival from an old-looking date or invent a year. The independent product audit uses the same notice decoder on its separately fetched payload and rejects a delayed variant as confirmed stock. Carry the notice through current cards and dated history; older observations without the field remain readable and are not rewritten.

## Taylor detail-page contract

Taylor's parent listing IDs differ from its purchasable SKU identities. `TaylorParser` decodes the page's JSON literal assignments without executing merchant JavaScript, checks canonical product identity and the explicit US-price container, and binds the selector SKU to its complete option query. Both single- and multi-SKU links were verified in an anonymous browser. Missing stock, backorders, factory-second levels, malformed prices and ambiguous option destinations cannot become offers. Detail breadcrumbs supply the authoritative category; listing names are only a request-saving prefilter.

Taylor's normal pagination is cumulative. Validate the requested page, page size, advertised total and unique listing IDs. Different listing IDs may alias one product URL; fetch that canonical detail only once. Show All must still match the advertised total and the bounded listing cap. Shared HTTP detail resolution is opt-in, paced, bounded and source-domain restricted. Any failed or malformed detail makes the entire source incomplete, preserving previous successful rows and observation timestamps. Keep prior Shopify/Grizzly validation intact.

## Rockler candidate contract

Rockler is not yet enabled. Its Searchspring sale category includes inline banner slots and full-price gift promotions. Request `disableInlineBanners=true` and validate the entire advertised product count, page sequence and unique IDs. Discovery titles are only a taxonomy prefilter; broad secondary category tags can mislabel equipment as accessories.

Bind a simple product's canonical URL, SKU, delivery-component ID, visible name/price and explicit USD/new-condition structured offer before using `/frx/stockmessage`. Confirmed stock requires the active Ready to Ship message and no active shipping estimate. Preserve manufacturer shipment notices, freight restrictions and unknown stock. The raw `backorder_date` alone is not active delivery evidence. Skip delivery requests for verified full-price promotions; never create exact offers from unconfigured bundles. The opt-in evidence fetch uses existing pacing and retry limits, rejects off-source URLs and does not follow redirects. HTTP 429 or malformed evidence makes the source incomplete. A complete fresh candidate refresh and separate merchant audit are required before enabling this retailer.

## Bike Closet contract

Use the public WooCommerce Store API, not authenticated merchant REST endpoints. Reconcile X-WP-Total / X-WP-TotalPages, requested page, unique parent IDs and the complete advertised variation set. Bind canonical storefront identity and condition/shipping text before decoding each variant's exact attribute query, USD minor units and stock/backorder fields. No cart action belongs in discovery or audit. A source's response-header validation is opt-in; existing parser pagination remains unchanged.

Merchant size conflicts cannot satisfy stock or fit: an explicit SIZE L title with an XS variant is excluded. Shipping qualifiers must resolve uniquely through the parent's actual size/color terms; ambiguous scope applies conservatively. Keep old-looking notices until the merchant removes them. Preserve final-sale, shipping-region and frameset-photo caveats. TIME's Time Frames category is explicit manufacturer evidence. Audits use separate parent and selected-variant reads; a long-running audit cannot be reported as satisfying the fixed M3 timing window.

## Ski Essentials exact-offer feed

Decode only collection identity from the public React Router indexed JSON stream; never execute merchant JavaScript. The public Boost feed must reconcile a stable total, page size, unique product IDs and terminal count. Read each sale price from `online_variant_prices` by exact SKU and require explicit USD metadata; the ordinary variant price can still be MSRP. Never copy a product-wide lowest price to every size. Bind verified option names to the storefront option query, preserving the canonical product URL separately. Exclude configurable `Bundle Product` entries. Confirm stock only with explicit available status, positive tracked quantity and deny-backorder policy. Unknown/conflicting stock cannot satisfy exact size. Complete-source and partial-snapshot guards remain unchanged.

## Beaver main purchase panel

Beaver Industrial Supply retains the Shopify feed and explicit USD currency check, but its exact-host parser resolves each eligible single-variant product through the ordinary product page. Scope identity, SKU, variant, quantity, visible sale/reference prices and stock to the main `product-info` panel; recommendation cards and quick-view inventory are not purchase evidence. Decode only the JSON literal in the observed `window.dpoData.product` assignment; never execute merchant JavaScript. Bind the singleton default variant to canonical path, hidden purchase form and USD structured offer. Unsupported variant shapes or disagreement make the source incomplete.

`available: true` is insufficient when the main panel says Usually Ships in 5-7 Days or Call for availability. Retain those as unknown stock with the merchant notice. Explicit sold-out/unavailable evidence removes the offer. Independently fetch both exact product JSON and the main product page during audits; malformed JSON stays inconclusive even if the HTML agrees. Failed refreshes preserve earlier successful observations. Source activation still requires a complete fresh candidate and independent merchant evidence.

## Bolton candidate contract

Bolton remains disabled while its warehouse-relocation banner restricts purchases to LTL freight without product-specific eligibility. A promised past restoration date and optional freight-service controls do not establish eligibility. Reject the active nonempty banner before admitting or renewing stock. The candidate parser binds canonical slug, product ID, model, USD single-unit current/reference prices, new condition and stock. Bulk prices never replace quantity-one prices. Configured category counts, unique identities and page sequence must reconcile; repeated or missing listings are incomplete, not silently deduplicated coverage. Seven observed categories reconcile, but that is not full-retailer coverage.

## RA Cycles variant stock

RA keeps Shopify discovery and USD checks but requires the canonical product page and separate public product JSON as evidence. Reconcile every feed, ProductGroup, stock-map and endpoint variant ID; bind SKU, exact option values, price/reference and destination. The main selected purchase input, variant JSON, active stock message and visible money must agree. Its theme renders cents in a separate `sup` element; do not turn $2,799 with 99 cents into $279999. Dormant stock templates cannot establish availability.

Positive quantity with available=true and virtual-warehouse=false is immediate stock. Virtual-warehouse delivery retains the stated delay as unknown. An available variant with zero quantity can expose an explicit Coming soon / reserve backorder panel; that remains unknown and carries the merchant notice. Explicit unavailable variants are excluded. Preserve applicable final-sale limitations. Missing or contradictory state makes the refresh incomplete, retaining earlier successful data and timestamps.

An explicit Frameset tag precedes a broader Mountain Bikes discipline after accessory/condition exclusions. Numeric-s frame labels such as 50s are valid raw dimensions and remain distinct from 50cm; never infer equivalent geometry. Audits reuse the independently fetched exact product JSON and refetch the selected product page, preserving inconclusive results and the fifteen-minute observation window.

## Snow source completeness before persistence

`protect_partial_snapshots(deals, previous, outcomes)` is the snow admission boundary before `upsert_deals`. A source with a nonzero `errors` value or any collection whose `status` is not `complete` is withheld even when its returned count is healthy or it has no previous rows. Preserve the original failure metadata; add `withheld_reasons: [incomplete_refresh]` and ensure run-status reporting cannot label a status-only failure successful. The existing count-collapse gate still applies independently.

Only accepted sources may renew deals, price history, selected offers or offer observations. Withheld rows retain their previous timestamps and age out normally. `--min-stores` must count accepted sources before persistence; a partial source cannot make an otherwise insufficient refresh publishable. Test the CLI with a temporary database: failed-source rows and all history remain byte-for-byte equal, complete-source history advances when the gate passes, and no rows advance when the accepted-source minimum fails. A large partial count is not proof of a complete refresh.

## Snow default ranking ties

Exact percentage off remains first in `_products_to_deals`, `selection_sql` and default card ordering. On a percentage tie, choose greater cash savings for variants in the same source currency. Mixed-currency card results group USD first, then the actual currency code, before comparing savings within that group; do not compare nominal USD and CAD amounts or invent exchange rates. Only then apply image/stable-identity fallbacks. Explicit alternative sorts remain unchanged. Verify the same selected variant price, reference and purchase URL after size/budget filters, count and pagination; slightly higher exact percentages must still beat greater cash savings.


## Tools primary equipment and included accessories

In the tools classifier, an explicit included-accessory suffix (`with`, `w/`, `including`) does not make a complete primary tool into a replacement part. Keep full-title condition checks and retailer accessory taxonomy first, then establish equipment identity from the primary title. A broad retailer category or a tool named later in the suffix cannot turn a stand, bag, case, guard, fence, base or guide into equipment. Preserve the observed Fixed-Base Router machine descriptor and Blade Right Circular Saw orientation without admitting replacement parts or standalone blades.

Keep explicit bare-tool and whole-tool kit metadata even when descriptive features intervene. An included blade/filter kit alone is not a whole-tool kit. Explicit fixed bundles expose Bundle; that label does not establish battery/charger contents or stock. Verify exact selected prices, variant links, unknown-stock exclusion and filtered counts through normalization/query. Before release, replay every affected captured feed and all existing public snapshot product classifications; review additions, removals and label changes, then use fresh source and merchant checks. Feed availability cannot override delayed purchase-panel stock.

## Welding equipment and shipping notices

Tools classification requires explicit welding-machine/plasma-machine taxonomy or precise machine tags. Broad Welders collections also contain standalone guns, wire feeders and wire feed units. Exclude primary components even when the retailer calls them TIG Welding Machine, while preserving actual Wire Feeder Welder identity and complete systems with explicitly included components. Manufacturer-prefixed machine tags may establish a fixed bundle only when the complete prefix binds to declared manufacturer evidence.

The shared availability dispatcher serves both Shopify ingestion and separately fetched merchant audits. Baker's body_html/description backorder notice overrides available=true; Cyberweld's auto_outofstock tag does likewise on its actual store.cyberweld.com host. Keep the existing Harvey decoder unchanged. Retain an observed notice, exact prices/options/variant destination and unknown status; never let it satisfy stock-only or exact-size requests. Service-parts shipping promises, rebates and gifts are not evidence of machine stock or direct price. Test prior-day history preservation and the negative stock control independently from positive audit accuracy.

`availability.shipping_notice(item: dict, variant: dict, url: str) -> str` returns an observed notice or the unchanged Harvey result. An unknown stock offer retains `VariantOffer.availability_note`; schema and history fields do not change. A missing notice with ordinary positive availability follows the existing parser path. A matching host plus explicit negative evidence yields unknown, while a lookalike host or unrelated service-parts sentence must not trigger this override. Required regressions bind feed and product.js descriptions to the same variant, check stock-only exclusion and every non-stock audit field, preserve the prior-day notice, and cover a complete welder with an included feed unit. Wrong: infer confirmed stock from available=true despite a backorder sentence. Correct: retain the sentence and withhold confirmed stock.

## Shared manufacturer aliases

`Catalog.brand_aliases` contains exact casefolded retailer labels with stable canonical targets. Use `manufacturer_name(..., brand_aliases=...)` consistently at ingestion, query and history comparison. Query projects card/facet labels without mutating stored sources; canonicalize incoming brand filters before counts/pagination and preserve original-brand free-text matching. Web forms and generated links use the canonical selection. Unknown labels stay unchanged and escaped; never infer manufacturers from retailer names or strip arbitrary suffixes.

History compares canonical manufacturer labels but retains every other exact product/variant guard. Never rewrite stored observations or freshness, and never canonicalize rows passed to the raw health fingerprint. Alias targets must be idempotent and keys unique. Verify mappings against primary manufacturer/merchant evidence and replay each alias group's full original population. Manufacturer aliases do not authorize merging product builds, subbrands, variants or prices.

## Lightweight electric-bike taxonomy

Mike's Bikes' `BIKES AND FRAMES/BIKES - ELECTRIC/ELECTRIC MOUNTAIN LIGHT WEIGHT` segment describes complete e-bikes, not bike lights. For the cycling accessory check only, interpret that exact anchored parent/segment with a slash-or-end boundary. Keep the original merchant taxonomy for categorization, normalization and history; preserve negative descendants such as LIGHTS, BATTERIES or ACCESSORIES. Do not globally strip Light words or override condition, kids or shipping exclusions. Regressions must preserve exact selected size, variant, prices and destination and include misleading/extended/unrelated category paths.

## Incycle complete-bike taxonomy

Incycle's generic `Sporting Goods` type needs source-bound evidence: only exact HTTPS `www.incycle.com/products/` URLs may use `TURBO & ELECTRIC BIKE`, or `BICYCLES` with observed MOUNTAIN/GRAVEL/ROAD/ACTIVE tags, to establish a complete bike. Keep existing condition, shipping and accessory exclusions ahead of admission; keep the existing frameset branch before complete-bike classification. An accessory primary title cannot borrow positive bike tags. Preserve original offers and options: `Default Title` cannot imply a frame size from the product name. The current shipping policy separates bike and frameset fees; a generic free-shipping banner is not evidence of free bicycle shipping. See `docs/tasks/incycle-source/` for observed fixtures and admission receipts.

## Manual tools and powered-tool accessories

A retailer's generic driver/saw/oscillating-tool wording does not establish a complete powered tool. Max Warehouse's exact Oscillating Tool Access taxonomy describes accessories; sanding pads and nutsetters remain components even with motor-speed or compatibility text. Point Driver, Hacksaw and Nut Driver identities require explicit powered-machine evidence on the primary product, before compatibility or included-accessory clauses. Power in Power Nut Driver is not such evidence. Explicit manual, non-powered or hand-operated wording on that primary identity overrides a positive powered word; included manuals and later compatibility wording do not change the machine identity. Preserve actual complete powered tools with included pads/bits and keep existing condition/accessory guards first.

Test the observed merchant types and exact offers, positive complete kits, and misleading compatibility before/after the primary identity. Replay the whole affected feed, review every changed classification, retain survivor prices/options/destinations and historical rows, then refresh/audit only the affected existing sources. A below-default-floor exclusion improves unrestricted browsing; it is not additional deep coverage or proof of a competitive metric lead. See `docs/tasks/tools-accessory-precision/`.

## Contender generated options

On exact `contenderbicycles.com` and `www.contenderbicycles.com`, `shopify.is_contender_generated_variant(variant, url)` identifies the observed bounded literal `#MWS Options <digits>` marker in variant title/option1–3 or the product.js options list. Exclude those generated records before constructing offers, prices, sizes, availability or product summaries. Ordinary MWS words, unmarked variants and other hosts keep their existing behavior. Do not strip the marker, merge IDs, guess a base or transfer generated price/reference/stock to an ordinary variant.

The independent product audit reuses the predicate and rejects marked old offers even when endpoint price/stock facts match. Ordinary variants retain the existing independent identity, currency, money, option and stock checks. A generated-only product disappears when no real discounted offers remain; a full-price or sold-out base cannot be revived by its generated sibling. Preserve raw source fields, exact surviving variant destinations, unknown-stock handling and percentage-first query selection/counts/size/pagination. Fresh successful source replacement removes old generated current offers; historical observations are not rewritten or aliased. Require source-scoped factual regressions and a full retained-feed/snapshot replay before refreshing/publishing only Contender.

## Merchant price notes

`VariantOffer.price_note` is optional string metadata with an empty default. `shopify.pricing_notice(item, url)` emits `Retailer asks you to contact them for current pricing.` only for exact Contender apex/www and the exact `contact-for-current-price` tag in a list or comma-separated string. The caveat does not establish quote-only inventory, unavailable stock, a different reference or additional negotiated savings. Keep all price/reference/stock/fit/destination and selection/ranking/count behavior unchanged; generated-option exclusions remain independent.

The independent product.js audit decodes current tags separately and compares the current note with the stored selected offer whenever either is nonempty. Missing/changed notes fail that agreement check while retaining ordinary price/stock checks; both-empty legacy audits keep their existing result shape. Catalog history projects `candidate.get('price_note', '')` from each dated matching variant, never from today's offer. Price notes do not change identity matching, schema or daily retention. Do not backfill older observations or interpret an unrecorded historical note as proof the merchant had no caveat then. Replay optional-note-only changes before a source-scoped refresh/publication.

Explain a normalized listing's disappearance only after checking raw product membership and exact variant prices/stock; absence from normalized results alone does not prove removal from the raw feed.

## Circle exact option formatting

Circle's quoted inner option lists are CSV inside strict outer JSON. Decode doubled quotes and embedded commas with strict CSV, preserving exact values; unquoted single labels retain their existing behavior. Validate the quoted-list syntax before CSV decoding because stdlib strict mode accepts bare quotes in unquoted fields. Malformed fields and duplicate dimensions fail. Do not repair JSON or strip quotes from offers.

Native exact-ID selection proves one narrow hidden-DOM omission: an API `size` matching `[1-9][0-9]*"` may compare with its exact numeric hidden label only when that quoted native selector value occurs once and no unquoted native alternative exists. Reject full option-tuple collisions across IDs after this comparison. Preserve quoted API output, all other dimensions and selected-form agreement, prices, references, stock, images and destinations. This exception does not establish arbitrary quote/unit equivalence or source completeness; failed/missing evidence and unrelated structural shapes remain unresolved.

Every Circle main form requires one quantity input with numeric `qty_<productID>` identity. Present purchase-button PID/VID evidence, including partial attributes, must agree with that identity and the exact selected cart action. Require one actual enabled Add to Cart button and reject disabled/aria-disabled, Out of Stock, non-button, duplicated or conflicting form controls even when API/schema stock is positive. A button alone never establishes confirmed stock. Missing button identity is supported only with the captured explicit OutOfStock panel and Out of Stock control plus independent selected API evidence: unavailable, not on stock, tracked, zero level, no backorders or delivery delay. Still reconcile every sibling separately; a sold-out selected default does not make the family unavailable. Reduced fixtures restore quantity fields from retained originals, never guessed IDs.

The no-dimension Default branch requires one native variant selector/selected ID and displayed matching price, no other selects, one exact hidden ID with literal Default color/size labels, and one matching API variant with title Default, boolean default=true and empty top-level variant. Keep all currency/money/stock/image/family/selected-ID checks. Output uses sizeNone and empty options; never infer One Size. Extra/mixed variants, controls, labels or conflicting default flags fail.

Circle may record factual `Product.product_type='Includes children sizing'` from its complete exact variant set. Match whole explicit ordered age labels only, with observed bounds years≤16, months≤24 and toddler codes≤10, including the observed height/alpha parenthesized age wrappers. A bare number, adult fit, height, inch size or trouser compound establishes no age. The captured bounded `ages … years, for a child` product-description clause may establish the same evidence. This is source-evidence containment metadata, not a claim about every sibling.

Miles' manufacturer chart applies only to exact merchant brand ID2212719, title Miles and canonical `/brands/miles/` URL, independently bound through the retained Miles the Label description. Only chart-supported numeric2–14 labels count; do not infer 6X or unknown/adult labels. Preserve every offer/name/size/stock/price/image/destination exactly, including contrary or unavailable siblings. Existing snow whole-family children exclusion consumes the marker conservatively; do not drop offers, manufacture age/fit equivalences, rewrite history or activate a source through this metadata. Reconcile every changed family and remaining apparel before admission.
