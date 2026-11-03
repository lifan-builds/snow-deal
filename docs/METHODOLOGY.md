# The Deal Aggregator methodology

## Core promise

Find amazing deals with the deepest percentage discounts across retailers, especially on products that were expensive to begin with. The experience should make an unusually good find immediately obvious: **70% off · originally $2,000 · now $600 · save $1,400**.

This is a discovery product for people willing to consider different brands, models, or previous seasons when the discount is exceptional. Product fit, reviews, and clean data help shoppers act on the opportunity. The default ranking is descending percentage off; review scores, affiliate commissions, and image availability must not outrank the discount.

The user clarified this priority on 2026-11-02. Running shoes were rejected as the next category because their typical purchase price does not fit the intended emphasis on expensive items.

## What Fresh Powder already demonstrates

- Search across specialist retailers instead of requiring shoppers to monitor many clearance pages.
- Normalize inconsistent listing names, prices, images, categories, and available sizes.
- Remove unrelated items and full-price listings before they enter the deal feed.
- Show original and current prices, percentage off, and absolute savings together.
- Make deep discounts browseable with category, brand, retailer, price, and fit filters.
- Attach expert reviews where a match is available; do not require a review to surface a deep discount.
- Scrape separately from serving, precompute review matches, and serve fast database queries through simple server-rendered pages.
- Track source health and freshness so a big discount does not hide a broken feed.

Fresh Powder currently sorts discounts first. This refactor corrected a hidden image-first sort that could put a smaller discount above a larger one. Existing review sorting remains an explicit shopper choice.

## Repeatable process

1. **Choose an expensive category with real clearance inventory.** Favor substantial reference prices, repeated deep markdowns, identifiable models, multiple specialist sellers, and a useful set of filters. Start with a narrow product scope, not every accessory sold by those stores.
2. **Build a source map.** Record retailer, listing URLs, currency, platform, condition, price basis, expected stock details, and the last successful verification. Prefer structured feeds and APIs where available; use HTML or browser adapters when needed.
3. **Normalize before ranking.** Preserve the same model, year, build, condition, and purchasable variant for the sale and comparison prices. A frameset is not a complete bicycle. One cheap size must not imply every size has that price.
4. **Calculate the discount consistently.** `100 × (reference_price - sale_price) / reference_price`; savings are `reference_price - sale_price`. The prices must use the same currency and describe the same item. Label MSRP/list-price comparisons honestly; they are not proof of the usual street price or an all-time low.
5. **Publish the deepest discounts first.** Keep percentage off as the default sort. Show original price, sale price, and savings together. Use category scope and optional reference-price floors to emphasize expensive products, rather than hiding a different ranking formula behind “percentage off.”
6. **Make the opportunity actionable.** Show available variants, condition, retailer link, and observation time. Add relevant fit and compatibility filters. Keep unknown shipping/tax costs separate from known item savings.
7. **Measure useful finds.** Track the count of usable deeply discounted high-ticket offers, source freshness, false discounts, variant accuracy, and outbound interest. Raw product count alone is not success.
8. **Expand only after the catalog works.** Add adapters and catalog rules, reuse shared ingestion, and preserve separate data and brand identities. Affiliate links can fund the service, but commissions do not change default ranking.

## Category selection

The user selected **premium cycling** and **workshop/power tools** for the next sites. Both now have working local storefronts with shared ingestion, persistence, querying, and presentation. See [Big Ring](../catalogs/cycling/README.md) and [Bench Drop](../catalogs/tools/README.md). Implementation alone does not prove repeat inventory quality or commercial demand.

A proposed experiment is to sample 3–5 retailers for two weeks and count available products with a reference price of at least $1,000 and a discount of at least 40%. These are research thresholds, not proven economics. Big Ring defaults to an optional $1,000 reference floor; Bench Drop defaults to $200. Both rank by percentage off. Compare more than one size and confirm that the listing price is actually available. Use the findings to guide source expansion.

## Implemented versus next

**Implemented and released:** shared product/retailer/variant models, Shopify ingestion, HTTP traversal, parser utilities, rate limiting, catalog separation, and percentage-first Fresh Powder ranking. Fresh Powder retains variant prices and dated observations; exact-size filtering selects a reported in-stock variant before ranking/counting. Original-price floors and explicit-title model-year filters are optional. Cards show currency, dollar savings, reference basis, selected options, and source time. Browser-local saved searches do not send emails. Refresh reports distinguish variant coverage and confirmed-size coverage from merchant accuracy.

**Still to validate or build:** broader variant coverage beyond the 7,836 products with reported in-stock sizes in the first release snapshot, independently verified reference-price/history claims, structured condition and shipping/return facts, public launch and recurring deployment for the new catalogs, and email alerts. Current percentages use retailer reference prices, not verified historical street prices. Variant observations cover discounted offers, not full inventory history. Keep different currencies separate; no exchange-rate conversion is implied. The [execution receipt](research/2026-11-02-deal-site-landscape/execution/IMPLEMENTATION.md) separates offline checks, bounded merchant observations, and the [completed rollout](RELEASE-RECEIPT.md).
