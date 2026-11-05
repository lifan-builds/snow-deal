# Implemented locally — 5 November 2026 UTC

Fresh Powder now chooses the greatest cash saving when exact percentage discounts tie, both when seeding an ingested deal and when selecting its eligible database variant. Default card order keeps exact percentage first, then USD first and other currency codes, then savings within that currency, then the existing image/identity fallbacks. Invalid sort input falls back to this complete default order. Explicit alternative sorts are unchanged. No exchange-rate conversion or nominal USD/CAD cash comparison is introduced.

Changed code: aggregator/offers.py selection_sql, aggregator/db.py default sort map/fallback, aggregator/scraper.py _products_to_deals best-offer key. Tests live in the existing test_offers.py. No source configuration, database schema, history writes or production files were changed.

Four new temporary-database regressions cover percentage ties, filtered alternate variants with correct purchase URLs, slightly greater exact percentages, legacy/variant-backed card order ahead of image availability, stable pagination/counts, explicit price sorts, and USD/CAD separation with explicit currency filters. Before implementation, the tied-variant and default-card-order regressions both failed; the exact-percentage-primary regression already passed.

Validation: the focused offer module passes 18 tests. An isolated copy of origin/main plus only this task's four owned Python changes passes the full 754-test public-release suite, with eight existing warning emissions. It excludes the concurrent inactive House candidate and its registry change. Validation copy: .local/source-expansion/snow-savings-ties-validation/. AST parsing and scoped whitespace checks pass. Ruff diagnostic comparison against HEAD shows zero new findings: offers 0/0, database 4/4, scraper 8/8 and offer tests 16/16 baseline/current. No type checker is configured.

Independent review, publication and live ordering verification remain required. The wider worktree contains concurrent House edits; those were preserved and excluded from this task's isolated release validation.
