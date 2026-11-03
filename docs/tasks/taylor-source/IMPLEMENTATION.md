# Taylor Toolworks source admission — 3 November 2026 UTC

Bench Drop's local follow-up now has **10 contributing retailers, 352 eligible listings and 22 listings at least 40% off**. Five retailers contribute a deep deal, up from four. Cycling remains at 16 retailers, 1,142 eligible listings and 87 deep deals. Floors remain $200 for tools and $1,000 for cycling; ranking remains percentage discount first. Counts are merchant listings, not deduplicated models or guaranteed checkout availability.

This follow-up is on `codex/taylor-source`. It does not change the separate pending publication approval for release `7798318`. Nothing in this follow-up has been pushed or deployed.

## Source and mechanism

The [Taylor power-tool collection](https://taytools.com/power-tools?ppg=65535&pn=1) returned all 1,917 advertised listing IDs, representing 1,913 canonical destinations. Existing catalog classification selected 186 unique product pages for paced detail requests. All 187 requests completed successfully. Twenty-two details contained discounts; 21 were accessories under the detail page's taxonomy and were excluded. The admitted grinder bundle was $269 against the retailer's $494.14 reference, or 45.6% off. That reference is not a verified historical selling price.

The common parser now supports a small optional product-detail step. Taylor listing cards only discover products; exact SKU JSON, readable options, the US price container, stock quantity and ordinary condition determine eligibility. Variant identity includes both selector SKU and option query. The shared fetcher deduplicates detail URLs, retains normal pacing and bounded retries, and rejects failed details or an exhausted detail budget. An incomplete attempt cannot replace a previous complete snapshot or renew its timestamp.

The source-specific parser never evaluates merchant JavaScript. Existing Shopify and Grizzly paths retain their destination guards. A narrow title guard avoids treating drill/router/driver bits as powered machines while retaining genuine powered tool kits.

## Verification

- **440 offline tests passed**, including 35 new Taylor regressions. Scoped Ruff and whitespace checks passed.
- The new source's qualifying offer matched a fresh merchant check, **1/1**. The combined catalog's top ten plus twenty seeded offers matched **30/30**, with no inconclusive results. A small mixed sample is not evidence of 99% population accuracy.
- Browser checks confirmed the grinder's price, stock text and enabled purchase control, plus a separate multi-SKU product's option URL. No cart or checkout action was taken.
- The combined standalone package and local preview have the same snapshot hash and report ten fresh configured sources. The Taylor-filtered card matches price, reference and purchase destination.
- Old source timestamps and observation history were preserved. No history was backfilled.

## Mobile task check

At 390×844 with empty browser storage, cycling's medium-size / $2,500 budget task returned 73 results, and tools' kit / $500 budget task returned 17. Both required four form interactions: open filters, set budget, choose fit/package, apply. Budget, fit/package and Apply controls were inside the viewport before interaction; all rendered result cards matched the requested fields and reported stock. This is local browser automation, not a user study or a literal tap/keystroke count. It does not prove a competitor-relative M9 win.

## Remaining work

Tools source breadth remains substantially behind the opportunity. A separate complete workshop probe checked 560 listings and 17 selected detail pages, adding no eligible equipment; it is not enabled. Other custom-storefront adapters and retailer-provided feeds deserve separate admission work; blocked sources remain unknown rather than empty. Production speed, competitor merchant samples and 30 real days of price history remain unfinished. The all-metrics lead claim still fails.

See the [durable request, audit and build receipts](../../benchmarks/2026-11-03-taylor-source.json) and [updated matrix](../../benchmarks/2026-11-03-taylor-matrix.json). The prior release's [publication plan](../../CATALOG-RELEASE-PLAN.md) remains unchanged. Review the follow-up locally at [Bench Drop](http://127.0.0.1:8769/).
