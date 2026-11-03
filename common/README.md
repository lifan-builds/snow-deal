# Common deal components

`deal_common` contains working code used by Fresh Powder and available to additional catalogs. It must not import a catalog.

| Component | Responsibility |
| --- | --- |
| `models.Product` | Raw product fields and percentage/dollar savings calculations |
| `offers.VariantOffer` | Variant identity, price/reference, size/options, stock evidence, and destination |
| `config.RetailerConfig` | Store identity, listing URLs, parser type, currency, platform settings |
| `parsers.base.BaseParser` | Listing extraction and next-page interface, with opt-in product detail resolution |
| `parsers.shopify.ShopifyParser` | Shopify JSON, available variants, prices, images, pagination |
| `parsers.grizzly.GrizzlyParser` | Public single-SKU JSON-LD, USD/new/stock/reference evidence, explicit page-count traversal |
| `parsers.taylor.TaylorParser` | Complete HTML listing discovery plus exact-SKU detail data, explicit option destinations and US price/stock evidence |
| `parsers.common` | Price parsing and product-name/URL cleanup |
| `http.fetch_products` | HTTP collection traversal, page caps, delay, caller-owned concurrency, HTTP failure handling |
| `rate_limit` | Request throttling for web endpoints |
| `catalog.definition` | Injected catalog identity, assets, sources, classification callback and defaults |
| `catalog.storage` | Catalog-bound SQLite snapshots, atomic source replacement and dated observations |
| `catalog.refresh` | Reused parser/HTTP ingestion, currency checks, scope and variant or exact-SKU validation |
| `catalog.query` | Freshness, matching-variant selection, filters, discount-first ranking, counts and pagination |
| `catalog.web`, `catalog.cli` | Read-only FastAPI/Jinja storefront, shared CSS/JS, source health and explicit refresh/serve commands |

Install through the root `pyproject.toml`. Source lives under `common/` so the public Python name is `deal_common`, avoiding collisions with generic packages named `common`.

## Catalog boundary

A catalog supplies retailer configurations and parser instances to the shared ingestion functions. It then applies its own eligibility rules, classification, attributes, review matching, and persistence. Shared code returns raw products; it does not silently discard a bike because it is not snow gear.

Fresh Powder retains the per-domain semaphore registry, browser extractor registry, categorizer, ski-length parsing, review sources, database schema, auth configuration, and branded templates. Shared HTTP code handles retries and collection outcomes. Catalog modules retain snow-specific assumptions or app policy. Its `StoreConfig` extends `RetailerConfig` with the legacy WA tax label. Existing import shims preserve `Product`, `BaseParser`, Shopify, parser helpers, and rate-limiter imports for older callers without duplicating implementations.

Cycling and tools now use the same snapshot/query/storefront runtime. Neither imports the Fresh Powder database, auth, tax labels, or reviews. Catalog-supplied assets and classification keep branded visuals and product scope out of common code. The shared query selects the eligible variant before ranking/counting/pagination and never constructs a price/reference pair from different offers.

## Adding a catalog

1. Record its scope and retailer evidence in `catalogs/<name>/README.md`.
2. Add a distinct Python package under `catalogs/<name>/src/` and register it in root package discovery. Do not reuse the historical `aggregator` package name.
3. Reuse `Product`, `RetailerConfig`, platform parsers, and `fetch_products`. Catalogs own retailer rosters and product scope. A retailer adapter shared by ingestion and independent auditing can live in common, provided it contains no catalog policy or imports; Grizzly is the current example.
4. Define exclusions, exact product identity, variant/condition handling, and category-specific filters. Capture deterministic fixtures before a live feed.
5. Add catalog tests to root pytest configuration and keep separate data paths, auth namespaces, and deployment configuration.
6. Validate real discounted inventory and freshness before enabling a scheduled scrape or public launch.

Run `.venv/bin/python scripts/check.py -q` from the workspace root.

## Probe a source before enabling it

Write a JSON array with `catalog`, `name`, `domain`, `scrape_urls`, and optional `parser_type` (`shopify` by default, `grizzly`, or `taylor`). Run `python scripts/probe_sources.py candidates.json --output .local/source-expansion/new-run --max-pages 30`. The output directory must be new. Inspect complete collection outcomes, eligible and ≥40%-off counts, condition/shipping restrictions and selected merchant offers before adding the source to a catalog. Keep raw public candidate snapshots local; retain a compact admission receipt in docs. See the [worked expansion](../docs/tasks/source-expansion/IMPLEMENTATION.md).

Taylor listings are discovery metadata only. The HTTP loop deduplicates canonical detail destinations and applies the catalog's existing classifier before fetching details; authoritative detail taxonomy is classified again before storage. Every detail request uses the normal pacing/retry policy. A failed detail, incomplete page, or exhausted 500-detail budget makes the source incomplete and preserves its previous successful snapshot. Other parsers retain their existing listing-only behavior.
