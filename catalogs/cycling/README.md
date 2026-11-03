# Big Ring — cycling deals

A working cycling storefront built on `common/deal_common/catalog/`. Scope: new complete mountain, road, gravel, electric, and other adult bikes, with framesets kept separate. The default retailer-reference floor is $1,000; users can change it. Percentage off always ranks first.

## Run from the workspace root

```bash
pip install -e '.[dev]'
cycling-deals refresh --database catalogs/cycling/data/catalog.db
cycling-deals serve --database catalogs/cycling/data/catalog.db --port 8766
```

Open http://127.0.0.1:8766/. Scraping is an explicit command; serving only reads the snapshot. A missing database produces an empty state. Data older than 24 hours is hidden.

## Catalog ownership

`src/cycling_deals/catalog.py` owns scope, classification, retailer definitions, copy, and defaults. `static/` inside that package owns the green/lime theme and bicycle artwork. Shared ingestion, storage, filters, ranking, pagination, templates, and saved searches live in `common/`.

The November 2 checkpoint enabled sixteen sources, adding The Path Bike Shop, INTENSE, Bike Mart, First Stop Board Barn, Colorado Cyclist, Planet Cyclery, Worldwide Cyclery, State Bicycle Co. and Fanatik Bike Co. to the original seven-source checkpoint. The November 2 follow-up snapshot has **1,142 qualifying in-stock listings, including 87 at least 40% off**, compared with 956 / 73 before this pass. Each source uses complete USD feeds and exact variant destinations. See the [saturation-pass receipt](../../docs/tasks/source-expansion/SATURATION.md) for source counts, separate merchant checks and remaining gaps.

Frame-size discovery ignores wheel-size dimensions. Unknown size remains unknown; SM/S, MD/Medium/M and LG/L aliases match, but geometry or rider fit is not inferred. Used, demo, display, refurbished, explicitly open-box, children's products, accessories and observed no-shipping tags are excluded. Explicit in-store-only/no-ship restrictions override positive shipping tags, and condition tags exclude open-box or cosmetically blemished stock even when titles omit it. Listing metadata does not establish every condition or destination-specific shipping fact. Check shipping, assembly and returns at the merchant.

The site includes search, category/brand/store/size filters, budget and discount floors, stock filtering, browser-local saved searches, and source health. References are retailer compare-at prices, not historical lows. [Original category research](RESEARCH.md) remains available; the planned two-week market experiment has not been completed.

Frame size requires both a recognized option name and a plausible frame-size value. Retailer color values mislabeled as Size and wheel-only dimensions remain in the full variant description but cannot satisfy exact-fit filters. The [latest verification](../../docs/benchmarks/2026-11-03-competitive-continuation.md) includes fresh affected-source pulls and a 30/30 merchant endpoint sample.

Big Ring is deployed at [bigring.clifan.com](https://bigring.clifan.com). See the [release receipt](../../docs/CATALOG-RELEASE-RECEIPT.md) for verified production state and [build instructions](../../docs/tasks/cycling-tools-sites/DELIVERY.md).

The current local configuration contains nineteen sources, including Gravity Coalition, Bike Closet and evo. [Bike Closet admission](../../docs/tasks/bike-closet-source/IMPLEMENTATION.md) contributes 19 sampled deep listings, with exact-size conflicts excluded and shipping notices retained. [evo admission](../../docs/tasks/evo-cycling/IMPLEMENTATION.md) adds 55 eligible listings, including three deep deals, after recognizing explicit complete-bike taxonomy and excluding store-only shipping. These follow-ups are not yet deployed; fresh release checks remain required.
