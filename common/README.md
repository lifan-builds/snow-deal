# Common deal components

`deal_common` contains working code used by Fresh Powder and available to additional catalogs. It must not import a catalog.

| Component | Responsibility |
| --- | --- |
| `models.Product` | Raw product fields and percentage/dollar savings calculations |
| `offers.VariantOffer` | Variant identity, price/reference, size/options, stock evidence, and destination |
| `config.RetailerConfig` | Store identity, listing URLs, parser type, currency, platform settings |
| `parsers.base.BaseParser` | Listing extraction and next-page interface |
| `parsers.shopify.ShopifyParser` | Shopify JSON, available variants, prices, images, pagination |
| `parsers.common` | Price parsing and product-name/URL cleanup |
| `http.fetch_products` | HTTP collection traversal, page caps, delay, caller-owned concurrency, HTTP failure handling |
| `rate_limit` | Request throttling for web endpoints |

Install through the root `pyproject.toml`. Source lives under `common/` so the public Python name is `deal_common`, avoiding collisions with generic packages named `common`.

## Catalog boundary

A catalog supplies retailer configurations and parser instances to the shared ingestion functions. It then applies its own eligibility rules, classification, attributes, review matching, and persistence. Shared code returns raw products; it does not silently discard a bike because it is not snow gear.

Fresh Powder retains the per-domain semaphore registry, browser extractor registry, categorizer, ski-length parsing, review sources, database schema, auth configuration, and branded templates. Shared HTTP code handles retries and collection outcomes. Catalog modules retain snow-specific assumptions or app policy. Its `StoreConfig` extends `RetailerConfig` with the legacy WA tax label. Existing import shims preserve `Product`, `BaseParser`, Shopify, parser helpers, and rate-limiter imports for older callers without duplicating implementations.

The second catalog should first prove which persistence and presentation behavior is identical. Extract those parts when there is a concrete second consumer; do not copy the entire Fresh Powder app or pretend its ski-length columns form a universal schema.

## Adding a catalog

1. Record its scope and retailer evidence in `catalogs/<name>/README.md`.
2. Add a distinct Python package under `catalogs/<name>/src/` and register it in root package discovery. Do not reuse the historical `aggregator` package name.
3. Reuse `Product`, `RetailerConfig`, platform parsers, and `fetch_products`; keep retailer-specific adapters in the catalog until they have a second consumer.
4. Define exclusions, exact product identity, variant/condition handling, and category-specific filters. Capture deterministic fixtures before a live feed.
5. Add catalog tests to root pytest configuration and keep separate data paths, auth namespaces, and deployment configuration.
6. Validate real discounted inventory and freshness before enabling a scheduled scrape or public launch.

Run `.venv/bin/python scripts/check.py -q` from the workspace root.
