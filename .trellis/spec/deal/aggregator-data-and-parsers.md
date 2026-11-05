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

## Snow admission before persistence

The current workspace contract lives in `docs/project-guidance/aggregator-data-and-parsers.md`, under Snow source completeness before persistence. `protect_partial_snapshots(deals, previous, outcomes)` must exclude a source with nonzero errors or any non-complete collection status before upsert/history writes, even with healthy counts or no baseline. Preserve prior timestamps and the independent collapse guard. A temporary-DB CLI regression must prove that failed-source deals, offers and observations remain unchanged, complete sources advance only when the accepted-source minimum passes, and receipts report the withheld reason. Large partial counts cannot establish completeness.

## Cash-savings tie contract

See `docs/project-guidance/aggregator-data-and-parsers.md` under Snow default ranking ties. Exact percentage is primary; greater cash savings break same-currency ties during ingestion, variant selection and default card sorting. Mixed-currency ties group USD first, then actual currency code, before savings; no implicit currency conversion. Filters/count/pagination must retain the chosen variant identity.


## Tools primary equipment recall

See `docs/project-guidance/aggregator-data-and-parsers.md` under Tools primary equipment and included accessories. Preserve full-title condition and existing accessory-taxonomy gates; an included blade/filter does not define the primary item. Require actual equipment identity before accepting an included-accessory suffix, preserve explicit whole-tool package labels and exact offers, and reconcile all existing public snapshot classifications plus changed feeds before release. Do not broaden taxonomy precedence from a single mislabeled merchant row.
