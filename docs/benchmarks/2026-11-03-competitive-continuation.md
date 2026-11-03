# Competitive continuation — 3 November 2026 UTC

These observations were collected on the evening of November 2 in Los Angeles. They supersede the local inventory baseline in earlier reports, without rewriting those reports. Changes remain local; no new catalog or snow change was published in this pass.

## Product improvements

- Tools now recognize jigsaws, oscillating tools and explicitly powered ratchets while retaining accessory and condition exclusions. The full nine-source refresh has **351 eligible in-stock listings, including 21 at least 40% off**, up from 347 / 20. Three newly admitted listings follow the classifier correction; a fourth is inventory movement during the refresh. All four matched separate merchant checks.
- Cycling retains **1,142 eligible listings and 87 at least 40% off across 16 contributing retailers**. Eleven retailers contribute a deep deal; do not confuse this with the 16 contributing retailers or configured connectors.
- Three Yeti listings at Pro Bike Supply have color values under the retailer's Size label. Cycling now withholds unrecognized frame-size values rather than inventing a correction from the Color option. Full variant descriptions and exact destinations remain visible. Bike Mart wheel-only values also stay outside the frame-size facet. Both affected sources completed fresh pulls. No eligible listing was lost to this correction.
- Snow ingestion and snapshot repair exclude explicit blem/blemished products from the same condition cohort used by cycling/tools. Repair preserves price and observation history. An adjustable demo-design binding is not necessarily used equipment: [evo's Marker Kingpin description](https://www.evo.com/products/228438-marker-kingpin-10-demo-alpine-touring-ski-bindings) describes adjustability, while [its blem guide](https://www.evo.com/pages/new-blem-condition) identifies manufacturer imperfections.
- Snow discovers its stylesheet earlier and loads the existing font stylesheet in parallel instead of through a nested import. In a controlled captured-content fixture, median LCP fell from **792 to 596 ms (25%)**, with identical first-price position and no horizontal overflow. This is local paired evidence, not a deployed improvement.

## Coverage evidence and limits

All counts use the existing reference floors ($500 snow, $1,000 cycling, $200 tools) and at least 40% off. These are listings, not independently deduplicated cross-retailer models. The [evidence receipt](2026-11-03-evidence.json) retains candidate rows, exclusion dispositions, page/API hashes and measurement timestamps.

| Surface | Inspected inventory | Deep equipment candidates | Candidate retailers | Qualification |
|---|---:|---:|---:|---|
| Fresh Powder public | 1,381 price-filtered listings | 967 | 14 | Source-reported in-stock equipment; two blem products removed from comparison; merchant checkout unverified |
| [Powder Deals](https://powderdeals.com/deals) | 497 listings / 21 complete pages | 34 | 4 | Exact variant and merchant stock unverified |
| Big Ring local | 1,142 eligible listings | 87 | 11 | Exact source variants; shipping/checkout not independently verified population-wide |
| [Velo Bargains](https://velo.bargains/deals) | 346 listings / 15 complete pages | 12 | 1 | Bikes/frames candidate cohort; merchant stock unverified |
| [MTB Price Agent](https://mtbprice.com/) | 734 public API records | 52 | 7 | Full-suspension subset; source claims new/in stock, price not independently tied to each size |
| Bench Drop local | 351 eligible listings | 21 | 4 | Exact source variants; shipping/checkout not independently verified population-wide |
| [HardHat Deals](https://hardhatdeals.com/) | 533 API records; 328 collapsed cards | 7 | 3 | Of 28 price-threshold candidates, seven match workshop/power-equipment scope; stock, seller and package remain unverified |

This does **not establish M1/M2 superiority**. In particular, all-cycling inventory cannot be compared directly to MTB Price Agent's suspension-specific subset. HardHat's grouped alternatives are not distinct visible cards. Competitor stock uncertainty is not zero inventory. Daily Tool Drops displayed eight offers; none crossed both our $200 reference floor and 40% discount, but that small visible snapshot is not a complete retailer audit.

[Ski Finder](https://www.ski-finders.com/deals) is the 21st service in the registry. Its inspected page had 33 deals and 312 skis, including history drops, cross-shop gaps and comparisons with a newer model year. Those reference bases must be separated before percentage comparisons. The previous machine-readable registry omitted HardHat despite listing it in the prose; the new matrix repairs that omission.

## Accuracy and history

The latest cycling and tools top-ten-plus-twenty-seeded merchant audits each matched **30/30**. [Cycling receipt](2026-11-03-cycling-merchant-audit.json) and [tools receipt](2026-11-03-tools-merchant-audit.json) retain identities, timestamps, response hashes and checks. Earlier inconclusive audits remain in the November 2 reports.

These tests compare merchant product endpoints for identity, currency, current/reference price, raw options and reported availability. They do not place orders, verify US shipping, independently prove historical reference values, or complete M4/M5. A 30/30 sample gives a descriptive Wilson 95% interval of roughly 88.65–100%; the mixed top-ten/random sample does not prove 99% population accuracy or superiority over competitors.

Both local catalogs have observations on **two actual UTC dates**. Thirty-day history coverage is still zero. There is no substitute for collecting real observations on at least 30 dates, and the new schedules are not deployed yet.

## Mobile measurements

Three cold production runs per site used installed Chrome in ephemeral contexts at 390 × 844, cache disabled, 150 ms latency, 1.6 Mbps down / 750 Kbps up and 4× CPU slowdown. All were collected in one session. LCP and maximum-session-window CLS were observed until eight seconds after the first price appeared. These are bounded lab measurements, not field percentiles. [LCP definition](https://web.dev/articles/lcp); [CLS session windows](https://web.dev/articles/cls).

| Production site | Median LCP, ms | Worst CLS | Initial scroll to price, px |
|---|---:|---:|---:|
| Fresh Powder | 1,712 | 0 | 0 |
| Powder Deals | 1,252 | 0.00007 | 318.2 |
| Ski Finder | 992 | 0.03329 | 0 |
| Velo Bargains | 2,004 | 0.00090 | 212.7 |
| MTB Price Agent | 3,796 | 0 | 739.1 |
| HardHat Deals | 1,348 | 0.09644 | 886 |
| Daily Tool Drops | 2,644 | 0.00349 | 0 |

Fresh Powder meets the absolute loading target but is behind both measured snow competitors. Zero-scroll discovery ties Ski Finder and Daily Tool Drops. Big Ring and Bench Drop local previews also need zero initial scroll, but their localhost loading times are excluded from competitive M10. Exact-fit task actions and responsiveness remain unmeasured. Failed pilot/selector observations are retained separately from the three successful runs.

## Verification and next constraints

405 offline tests pass. Scoped Ruff and whitespace checks pass. Both final standalone packages and running previews match their expected snapshot hashes, return healthy source states, and serve the tested pages. Package paths: `.local/catalog-preview/bigring-competitive-final/` and `.local/catalog-preview/benchdrop-competitive-final/`. Builds contain explicit public snapshot data only.

The [new matrix](2026-11-03.json) keeps M1/M2 candidate counts provisional, missing accuracy cells unknown, local speed out of competitive claims, and old observations on their original dates. `scripts/benchmark.py docs/benchmarks/2026-11-03.json --require-lead` must still fail: the overall goal is not achieved.

Next meaningful work is publishing the prepared release after scoped approval, collecting real history, expanding retailer adapters beyond the reusable-feed queue, and independently measuring comparable competitor variants and exact-fit tasks. The [release plan](../CATALOG-RELEASE-PLAN.md) defines the concrete publication scope. Source expansion has diminishing returns within the probed feed queue; the broader competitive goal has not saturated.
