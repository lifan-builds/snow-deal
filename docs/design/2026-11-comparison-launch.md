# Comparison and search launch — November 1, 2026

Implementation of the first release from [the competitor audit](2026-11-competitor-search-audit.md). Production code commit: `823748e`.

## Shipped

- 24 model/year comparison pages backed by 98 reviewed retailer references, linked from `/products` and matched deal cards.
- Exact reported-size filtering, separate USD/CAD views, retailer timestamps, direct shop links and explicit unknown-size handling.
- Observed price history with an accessible chart/table once multiple days exist. One day is explicitly insufficient for a rare-deal or 30-day-low claim.
- 13 brand directories; the five with multiple reviewed models are indexable (Atomic, Nordica, K2, CAPiTA and Ride). Single-model directories remain navigable but noindex.
- `/how-it-works`, product and breadcrumb structured data, website identity, canonical URLs and a 41-URL sitemap (previously 10).
- Search Console ownership verification on the production custom domain.

## Data safeguards and catalog maintenance

`comparison_catalog.json` records the exact reviewed URL, normalized full title, category and history start for each reference. Runtime matching requires all identity fields to agree. Different model years, women's models, bundles and width variants must not be merged through fuzzy matching.

Only the latest store snapshot and observations no older than 72 hours qualify as current offers. A reused retailer URL cannot pull earlier prices into a newly reviewed model's history. Currency is never converted or combined. Size filters require explicitly reported sizes; ranges do not imply every intermediate size is in stock. Retailer listing prices can still vary by size, shipping and tax, which the page explains.

To expand coverage, inspect candidate public retailer listings, confirm model/year/category/variant identity, then add exact references and their reviewed observation start. Recheck renamed titles instead of relaxing matching. Keep pages available when current offers disappear, without publishing empty AggregateOffer markup.

## Verification

- 135 tests passed, including eight comparison tests covering matching, freshness, currency, sizes, bounded history, routes, schema and card links.
- JavaScript syntax, Python compilation and diff whitespace checks passed.
- All 24 production product pages returned HTTP 200 with correct canonicals and structured offer counts matching rendered offers; no failures.
- Production directory, brand, methodology, home and sitemap endpoints returned HTTP 200.
- Browser checks covered desktop, a 390-pixel mobile viewport with no horizontal overflow, and a size filter that correctly narrowed Atomic Bent 100 2026 to the retailer reporting 179 cm.
- Vercel reported successful production deployment for `823748e`.

## Google receipts and limits

Search Console confirmed ownership of `https://freshpowder.clifan.com/` using the deployed HTML tag. Keep that public tag in place to retain verification.

Sitemap submission succeeded. The submitted-sitemaps table reported **Success**, **41 discovered pages**, and a November 1, 2026 last-read date. This is discovery, not confirmation that every URL is indexed.

Homepage inspection reported **URL is on Google**, **Page is indexed**, successful smartphone crawl, indexing allowed, and the inspected custom-domain URL as Google's selected canonical.

The new `/products` directory was not indexed at inspection time. Its separate manual indexing request failed with Google's message that the reCAPTCHA service could not connect; no successful indexing-request receipt was obtained. The successful sitemap submission remains intact. Aggregate Search Console reports were still processing; no ranking, click or Core Web Vitals improvement is claimed.

## Remaining work

- Review Search Console indexing and query/page performance once data appears; measure outcomes before claiming ranking gains.
- Expand reviewed model coverage and accumulate real price history before implementing historical rare-deal ranking.
- Add evidence-based deal analysis and factual operator/contact information; do not invent hands-on reviews or shipping costs.
- Email delivery remains deferred at the user's request. Signup remains email-only and explicitly advertises alerts as coming soon.

This release closes the comparison-page and crawl-discovery gaps. It does not complete every item in the broader competitive strategy.
