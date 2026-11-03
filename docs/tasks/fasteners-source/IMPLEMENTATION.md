# Fasteners Inc admission — 3 November 2026 UTC

Bench Drop's follow-up now has **11 contributing retailers, 409 eligible listings and 26 listings at least 40% off**, with six retailers contributing a deep deal. This adds 57 eligible listings and four deep deals to the Taylor checkpoint. Compared with the unchanged nine-source publication candidate `7798318`, Taylor plus Fasteners add 58 eligible listings and five deep deals. Cycling remains at 16 retailers, 1,142 eligible listings and 87 deep deals. All counts use the existing reference floors, reported stock and percentage-first ordering.

## Reusing the existing ingestion mechanism

The [Fasteners storefront](https://fastenersinc.net/) requests product data from its public `fastenersinc.myshopify.com` store. That store exposes the standard anonymous Shopify collection feeds. No new parser, client credentials or privileged API integration was needed. Discovery enumerated 905 collection records and selected five equipment/closeout collections. All five completed: 19 JSON product pages plus five collection/currency checks, with USD confirmed throughout. Overlapping collections are deduplicated by canonical product URL.

The resulting source contains 75 discounted equipment listings before the $200 reference floor; 57 qualify above that floor and four are at least 40% off. The qualifying products each had one feed variant. Existing stock, condition, accessory and destination guards remain enabled. Review of their merchant tags/descriptions found no explicit pickup-only, used, refurbished or open-box restriction; that is not independent proof of every condition or shipping term.

Browser checks followed the actual offer URLs through the merchant's redirect to `fastenersinc.net/product/<handle>`. All seven checked destinations retained their variant query and matched the numeric price, reference and stock text. Four were the deep-discount offers; the others included a combo kit, a Makita bare tool and a FLEX kit. Some pages separately advertise free-tool eligibility; only the ordinary numeric per-item price enters our discount calculation. No cart or checkout action was taken.

## Data quality corrections

The title accessory guard rejected a genuine DEWALT jigsaw because its specification says “Blade Stroke Length.” The narrow correction permits that specification while preserving exclusions for replacement blades and blade taxonomy. It recovered a $119 jigsaw against a $239 retailer reference, or 50.2% off.

A cordless planer remains a portable power tool when “Cordless” follows “Planer” in its title. Package and battery-platform labels still require explicit evidence; SKU naming alone does not establish them. Five regression cases cover these corrections and nearby accessory negatives. Reclassification found no category changes among the preceding ten-source snapshot's retained listings.

## Verification and limits

- **445 offline tests passed**, scoped Ruff and whitespace checks passed.
- Fasteners' top ten plus twenty seeded merchant-product checks matched **30/30**. The combined 409-listing catalog also matched **30/30** with no inconclusive checks. These are two mixed samples, not 60 independent randomly sampled listings or proof of 99% population accuracy.
- The standalone package and preview report 11 fresh sources with matching snapshot hashes. All four rendered Fasteners deep-deal cards have the expected numeric prices, references and exact variant destinations.
- The combined snapshot preserves preceding source timestamps and real observation history. No operational database or deployment state was used.
- The refreshed local mobile task returns 19 kits within a $500 budget in four form interactions, with the necessary controls visible at 390×844 and no horizontal overflow. Cycling's medium-size / $2,500 task remains 73 results in four form interactions. This does not measure physical taps, typing effort or real-user success rates.

Current evidence is in the [admission receipt](../../benchmarks/2026-11-03-fasteners-source.json) and [updated competitive matrix](../../benchmarks/2026-11-03-fasteners-matrix.json). Review the local [Bench Drop preview](http://127.0.0.1:8770/).

This remains unpublished follow-up work after `dbea14b`. Release `7798318` and its pending publication approval remain unchanged. Broader source coverage, competitor merchant samples, production performance and 30 real observation days remain genuine gaps; this is not all-market saturation or proof that we lead every metric.
