## Project guidance

- This repository is the Deal Aggregator workspace. `common/deal_common/` owns reusable category-independent code; `catalogs/fresh-powder/` owns the existing snow product. `catalogs/cycling/` owns Big Ring and `catalogs/tools/` owns Bench Drop. The two new catalogs are locally built; publication is separate.
- The core promise is deep percentage discounts on expensive products. Default ranking must put percentage off first; reviews, images, or commissions must not outrank it. Read `docs/METHODOLOGY.md` for the product contract.
- Select a matching variant before filtering, sorting, counting, and pagination. Its price, reference, size, stock status, and purchase link must agree. Unknown stock cannot satisfy an exact-size request. Retailer reference prices are not independently verified historical selling prices.
- Fresh Powder's primary app is `catalogs/fresh-powder/src/aggregator/`; its secondary CLI and userscript live in the same catalog. Common code must not import a catalog.
- Use the relevant architecture, parser, web/deployment, and verification contracts in `docs/project-guidance/`.
- Install once from root with `pip install -e '.[dev]'`. Run offline checks with `.venv/bin/python scripts/check.py -q`.
- Preserve `catalogs/fresh-powder/PLAN.md` and `catalogs/fresh-powder/history/aggregator/PLANS.md` as product planning/history records. Track workspace changes in `PLANS.md`.
- Never read, stage, mutate, or publish ignored credentials, browser state, deployment state, or database files during generic validation.
