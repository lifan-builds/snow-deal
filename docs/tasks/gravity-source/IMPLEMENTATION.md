# Gravity Coalition cycling source — prepared locally

Competitor research identified Gravity Coalition as a missing merchant. Two complete public Shopify collection pages returned 226 parsed listing occurrences, deduplicated into 38 accepted discounted products. With the standard $1,000 reference floor and reported stock, 29 listings qualify and six are at least 40% off. The top eligible frameset is 61.7% below its retailer reference.

All 29 qualifying listings matched independent merchant product endpoints for exact variant identity, currency, price, reference, options and stock, with zero mismatches or inconclusive checks. Five-second request pacing was used. A second complete source refresh after classification fixes preserved every offer identity and value. This is local endpoint evidence, not checkout or historical-reference verification, and not production-runner admission.

Two category defects were fixed: Rocky Mountain's brand name could misclassify a gravel bike as a mountain bike; an explicit Frame Only listing could be classified as a complete mountain bike. Six deterministic regression cases cover these findings and related exclusions. All 451 offline tests pass.

The configured cycling catalog now has 17 sources in this local branch. This change is not part of approved release 7798318 and has not been pushed or deployed. It sits after the unpublished Taylor Toolworks and Fasteners work. Production rollout recovery and the Grizzly quarantine must be integrated before preparing the next release.

Evidence: `docs/benchmarks/2026-11-03-gravity-source.json`, `2026-11-03-gravity-merchant-audit.json`. Explicit task-owned public snapshots remain under `.local/source-expansion/competitor-audit/gravity-probe/` and `gravity-classified/`.
