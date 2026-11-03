# Gravity Coalition cycling source — prepared locally

Competitor research identified Gravity Coalition as a missing merchant. Two complete public Shopify collection pages returned 226 parsed listing occurrences, deduplicated into 38 accepted discounted products. With the standard $1,000 reference floor and reported stock, 29 listings qualify and six are at least 40% off. The top eligible frameset is 61.7% below its retailer reference.

All 29 qualifying listings matched independent merchant product endpoints for exact variant identity, currency, price, reference, options and stock, with zero mismatches or inconclusive checks. Five-second request pacing was used. A second complete source refresh after classification fixes preserved every offer identity and value. This is local endpoint evidence, not checkout or historical-reference verification, and not production-runner admission.

Two category defects were fixed: Rocky Mountain's brand name could misclassify a gravel bike as a mountain bike; an explicit Frame Only listing could be classified as a complete mountain bike. Six deterministic regression cases cover these findings and related exclusions. All 451 offline tests pass.

The configured cycling catalog now has 17 sources in this local branch. This change is not part of approved release 7798318 and has not been pushed or deployed. It sits after the unpublished Taylor Toolworks and Fasteners work. Production main through `0530cad` is now integrated, including the Grizzly quarantine, visible coverage notice, pinned Ruff 0.17.3 and bounded merchant-audit retries. Taylor's audit uses the same retry helper. The combined branch passes 454 offline tests, exact CI lint plus changed parser/HTTP checks, JavaScript syntax and whitespace checks. A fresh combined source refresh and production-runner admission remain necessary before the next publication.

Evidence: `docs/benchmarks/2026-11-03-gravity-source.json`, `2026-11-03-gravity-merchant-audit.json`. Explicit task-owned public snapshots remain under `.local/source-expansion/competitor-audit/gravity-probe/` and `gravity-classified/`.

## Admission correction

The earlier 38 accepted products included eight low-priced accessories whose broad retailer types still contained the word Bike. Browser inspection of the expanded facets exposed locks, pumps, computers, lights, a tire liner and parts. Explicit accessory taxonomy now takes precedence. The repeated full source traversal accepts 30 products and preserves all 29 eligible listings and six deep deals exactly. Cable lengths and tire dimensions no longer qualify as frame sizes. The original receipt is retained as superseded evidence, not silently rewritten. Fresh combined admission and the next publication scope are in `docs/SOURCE-QUALITY-RELEASE-PLAN.md`.
