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
- A failed store scrape losing over 70% of a prior 20+ item snapshot is withheld from replacement. Retained rows keep their original timestamps and expire after 72 hours; no stale price is relabeled as freshly checked.

## Source connections

Level Nine's configured catalog redirects to `https://www.backcountry.com/campaign/backcountry-outlet` (observed in Chrome). Retired the separate store entry and added the outlet ski and snowboard collections to Backcountry, deduplicating product URLs within that store. The outlet ski collection displayed 681 results during this audit.

MEC presents a verification page / HTTP 403. Keep its failure visible; do not treat a challenge or empty extractor result as a successful refresh. No CAPTCHA bypass, credentials, or alternate proxies are used.

The prior CI run had repeated HTTP 429 responses across Shopify feeds. Feed jobs are serialized across Shopify stores to reduce bursts; existing request pacing/retries and Retry-After handling remain. Improvement must be confirmed by a fresh CI scrape, not assumed from code changes.

## Validation

117 offline regression tests passed before the live refresh. Browser extractor JavaScript syntax checks passed. Tests cover real title/image/size fixtures, source errors, malformed feeds, pagination, exclusions, finite prices, stale filter counts, and failed-snapshot retention. No production auth data is used.

Live refresh and before/after measurements: pending.
