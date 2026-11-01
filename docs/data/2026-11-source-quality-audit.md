# Source quality audit — November 1, 2026

Baseline: public snapshot / scrape run 41303625448, checked 2026-11-01T12:16:45Z. It returned 8,848 deals from 26 of 28 configured stores, with 318 missing categories, 457 missing images, and 3,994 missing sizes. The old missing-length counter included clothing and accessories and is not a useful baseline for ski length coverage.

## Confirmed defects and corrections

- BlueZone, Colorado Discount and Sacred Ride parsers discarded listing images. Preserve lazy/regular image URLs and resolve relative paths.
- Colorado Discount selected a shortened image label instead of the product title. Use the product-name link and retain explicit centimeter sizes in that title.
- Shell pants/bibs were classified as jackets; ski suits and skis bundled with bindings were classified as hardgoods/bindings. Prefer product-name evidence to collection paths and apply specific garment/package rules.
- Substring exclusions could drop CAPiTA and block model fallback for Unleashed. Use normalized word boundaries, retain explicit Vans/Adidas snowboard boots, and keep non-snow exclusions.
- Shopify silently stopped at page 10 regardless of the configured 25-page limit. The orchestrator now owns the budget, records limits, checks malformed feeds and repeated pages, and preserves successful collections when another fails.
- Shopify color-only options were treated as sizes. Named size options take precedence; unnamed options require recognizable size values. Select a variant-associated image when provided.
- Backcountry's next-page selector could choose a previous page. The generic fallback never ran for sources with no explicit selector. Fix both, use exact page numbers, and report navigation failures/repeated pages.
- Backcountry's first image could be a promotional badge. Prefer its product image and retain the explicit retailer brand.
- Browser conversion discarded extracted metadata and accepted invalid URLs/prices. Preserve sizes/type/brand and reject malformed/non-finite prices and invalid product links.
- Source outcomes now include collection URLs, pages, product counts and failure types. Length completeness uses skis/snowboards as its denominator. Brand/category/length counts exclude stale and historical rows.
- An unexplained store count drop over 70% against a recent 20+ item snapshot is withheld from replacement. Retained rows keep their original timestamps and expire after 72 hours; no stale price is relabeled as freshly checked.

## Source connections

Level Nine's configured catalog redirects to `https://www.backcountry.com/campaign/backcountry-outlet` (observed in Chrome). Retired the separate store entry and added the outlet ski and snowboard collections to Backcountry, deduplicating product URLs within that store. The outlet ski collection displayed 681 results during this audit.

MEC presents a verification page / HTTP 403. Keep its failure visible; do not treat a challenge or empty extractor result as a successful refresh. No CAPTCHA bypass, credentials, or alternate proxies are used.

The prior CI run had repeated HTTP 429 responses across Shopify feeds. Feed jobs are serialized across Shopify stores to reduce bursts; existing request pacing/retries and Retry-After handling remain. Improvement must be confirmed by a fresh CI scrape, not assumed from code changes.

## Validation

127 offline regression tests passed, including execution of the actual pagination JavaScript against HTML-style and query-style link fixtures. Browser extractor JavaScript syntax checks passed. Tests cover real title/image/size fixtures, source errors, malformed feeds, pagination, exclusions, finite prices, stale filter counts, and failed-snapshot retention. No production auth data is used.

First full refresh completed and production was verified: [run 41351157773](https://github.com/lifan-builds/snow-deal/actions/runs/41351157773), revision `623f417`, snapshot checked at `2026-11-01T21:50:55.474822`. It published 12,222 deals from 26/27 stores, with 21 missing images, 348 missing categories (2.85%), and 65.0% size coverage. All Shopify collections completed without errors. Earlier audit runs were cancelled before publication.

Additional live catalog check: Skirack's structured `product_type` explicitly identified running shoes and bikes whose model-only names did not. Filtering now uses retailer type/vendor evidence as well as title/URL, including children’s product types. The House exposes ski/snowboard category and stock fields; discard other sports and out-of-stock items, and do not invent prices from "up to" discount percentages. Manual page-offset sources remain exempt from automatic pagination. Brand recovery only prefixes recognized literal brands, preserving numeric and multiword names.

## Follow-up from the live report

The Circle dropped from 190 deals to 8 because the revised page-number fallback did not accept `page2.html`. Restored that format, restricted fallback links to the same collection, and added executed JavaScript fixtures. Large unexplained per-store drops now trigger snapshot retention even when HTTP requests succeed; baselines older than 72 hours are ignored to avoid permanent quarantine.

Backcountry and Peter Glenn reached 25-page limits. The daily workflow now allows 100 pages per collection within a 90-minute job limit. Ski Essentials exposes a SHOW MORE button after its first 48 items (1,142 skis shown by the live catalog); follow it and verify that new cards arrive, reporting partial results on failure. Removed demo-only collection URLs. The House exposes a public next-grid URL; follow it dynamically instead of maintaining guessed page offsets. A live next-grid probe returned 240 products and another next-page link.

The refresh CLI and workflow accept selected retailers. A targeted follow-up for The Circle, Backcountry, Peter Glenn, Ski Essentials and The House is pending. Other store snapshots and price history remain intact.
