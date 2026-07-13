# Aggregator data and parser contracts

## Parser pipeline

All I/O is async. New static parsers inherit the parent `BaseParser` and import shared `parse_price()` from `aggregator/aggregator/parsers/common.py`; do not create parser-local copies. Browser extractors remain `(wait_selector, js_extract, next_page_selector)` entries, use `forEach` for NodeLists, and prefer `domcontentloaded` for anti-bot sites.

Every product path must preserve `image_url`, price, category, brand, and size/length behavior. Image extraction uses Shopify `images[0].src` or browser `data-src || src`. Price parsing must accept decimal and whole-dollar comma prices.

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
