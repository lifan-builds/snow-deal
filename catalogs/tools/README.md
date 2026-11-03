# Bench Drop — workshop and power-tool deals

A working tools storefront built on `common/deal_common/catalog/`. Scope: power tools, combo kits, and substantial workshop equipment. The default retailer-reference floor is $200; users can change it. Percentage off always ranks first.

## Run from the workspace root

```bash
pip install -e '.[dev]'
tool-deals refresh --database catalogs/tools/data/catalog.db
tool-deals serve --database catalogs/tools/data/catalog.db --port 8767
```

Open http://127.0.0.1:8767/. Scraping and serving are separate. Snapshots are read-only during serving, and offers older than 24 hours leave browsing.

## Catalog ownership

`src/tool_deals/catalog.py` owns scope, classification, package and explicit battery-platform rules, retailers, copy, and defaults. Its `static/` folder owns the charcoal/orange theme and drill artwork. Shared code lives in `common/`.

Nine sources are enabled: Tool Nut, Woodcraft, Craft Supplies USA, Harvey Woodworking, WEN, Factory Direct Supply, Grizzly Industrial, Max Warehouse and OakTree Supply. Tool Nut and Woodcraft now cover broader collections. The first-party USD feeds use exact variant destinations; Grizzly uses public JSON-LD with exact SKU destinations and verified pagination. The November 3 UTC follow-up snapshot has **351 qualifying in-stock listings, including 21 at least 40% off**, after adding recognition for jigsaws, oscillating tools and powered ratchets. These are dated observations, not guaranteed checkout availability. See the [competitive continuation receipt](../../docs/benchmarks/2026-11-03-competitive-continuation.md) and earlier [source saturation pass](../../docs/tasks/source-expansion/SATURATION.md).

Bare tools, kits, and unspecified packages have separate labels. Explicit Milwaukee M12/M18, DeWalt 20V MAX/FLEXVOLT, and Makita LXT/XGT title evidence can supply platform filters; voltage alone cannot establish compatibility. Empty size/platform filters are hidden. Package contents, machinery voltage/phase, shipping and returns still need merchant confirmation.

Accessory jigs, templates, rests, consumables, standalone batteries/chargers, and explicitly used/refurbished/open-box goods are excluded. Titles/types do not establish every condition fact. References are retailer compare-at prices, not independently verified street prices.

Max Warehouse's independent checks recovered from the earlier HTTP429; its 21 qualifying listings add no 40%-off deals. OakTree adds 11 such deals, all checked against separate merchant product data. Showroom machines are excluded. Access-restricted large retailers and sources requiring different SKU/stock adapters remain coverage gaps; the researched queue does not establish complete market coverage.

See [build and launch instructions](../../docs/tasks/cycling-tools-sites/DELIVERY.md). No public deployment has been performed for this catalog.
