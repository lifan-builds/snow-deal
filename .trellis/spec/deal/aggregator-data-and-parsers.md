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

Current shared catalog welding classification, negative stock precedence and history contracts are in `docs/project-guidance/aggregator-data-and-parsers.md`, under "Welding equipment and shipping notices". Read that section before changing the source-scoped availability dispatcher or tools machine/component classifier.

See `docs/project-guidance/aggregator-data-and-parsers.md` under Shared manufacturer aliases for the catalog-owned exact mapping contract. Ingestion, query/forms and history use the same identity helper; raw snapshots, fingerprints, variant guards and observation times remain unchanged. Preserve unknowns and intentional subbrands, and replay complete alias groups before release.

See `docs/project-guidance/aggregator-data-and-parsers.md` under Lightweight electric-bike taxonomy before changing accessory-keyword handling of hierarchical categories. Exact positive segments cannot hide negative descendants or rewrite merchant evidence.

## Manual tools and powered-tool accessories

A retailer's generic driver/saw/oscillating-tool wording does not establish a complete powered tool. Max Warehouse's exact Oscillating Tool Access taxonomy describes accessories; sanding pads and nutsetters remain components even with motor-speed or compatibility text. Point Driver, Hacksaw and Nut Driver identities require explicit powered-machine evidence on the primary product, before compatibility or included-accessory clauses. Power in Power Nut Driver is not such evidence. Explicit manual, non-powered or hand-operated wording on that primary identity overrides a positive powered word; included manuals and later compatibility wording do not change the machine identity. Preserve actual complete powered tools with included pads/bits and keep existing condition/accessory guards first.

Test the observed merchant types and exact offers, positive complete kits, and misleading compatibility before/after the primary identity. Replay the whole affected feed, review every changed classification, retain survivor prices/options/destinations and historical rows, then refresh/audit only the affected existing sources. A below-default-floor exclusion improves unrestricted browsing; it is not additional deep coverage or proof of a competitive metric lead. See `docs/tasks/tools-accessory-precision/`.

## Contender generated options

See `docs/project-guidance/aggregator-data-and-parsers.md` under Contender generated options. The exact-host Shopify predicate excludes bounded `#MWS Options <digits>` variant title/option markers before offer construction and is reused by independent audit rejection. No marker stripping, ID merging, base inference or price/reference/stock transfer is permitted; ordinary hosts/words/variants and all surviving exact offer fields remain unchanged. Test generated-only, inflated-reference, sold-out/unknown bases, query rank/count/size/pagination and old-audit controls. Replace current source rows only after complete source/audit gates and retain all history unchanged.
