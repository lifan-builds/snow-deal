# Cycling and tools source expansion — November 2, 2026

This is the earlier checkpoint. See the [subsequent saturation pass](SATURATION.md) for the newer roster, counts and candidate dispositions.

Implemented in `codex/cycling-tools-sites`, locally only. The user asked to reuse Fresh Powder's specialist-retailer expansion method. Existing dirty work was preserved; no push, deployment or operational database access occurred.

## Measured result

| Catalog | Contributing retailers before → after | Eligible listings before → after | Listings ≥40% off before → after |
| --- | ---: | ---: | ---: |
| Big Ring | 3 → 7 | 309 → 956 | 32 → 73 |
| Bench Drop | 2 → 7 | 175 → 213 | 7 → 9 |

These are dated local merchant listings, not unique models across stores. Every count requires confirmed stock and the existing retailer-reference floor: USD1,000 cycling, USD200 tools. Percent off remains the primary ranking. Counts exclude shipping/tax; retailer references are not proven historical selling prices. Earlier existing-source snapshots were retained with their actual timestamps; new sources were imported from completed candidate snapshots without making old observations appear new.

| Added source | Eligible listings | ≥40% off | Complete collection pages | Separate merchant sample |
| --- | ---: | ---: | ---: | ---: |
| [ERIK’S](https://www.eriksbikeshop.com/collections/cycling-bicycles) | 92 | 5 | 2 | 3/3 matched |
| [Pro Bike Supply](https://www.probikesupply.com/collections/on-sale-bikes-frames) | 357 | 13 | 3 | 3/3 matched |
| [Contender Bicycles](https://contenderbicycles.com/collections/sale) | 182 | 23 | 2 | 3/3 matched |
| [Cambria Bike](https://cambriabike.com/collections/mtb-bikes) | 16 | 0 | 5 across two collections | 3/3 matched |
| [Craft Supplies USA](https://woodturnerscatalog.com/collections/wood-lathes) | 1 | 0 | 1 | 1/1 matched |
| [Harvey Woodworking](https://www.harveywoodworking.com/collections/all) | 11 | 0 | 1 | 3/3 matched after earlier HTTP429 |
| [WEN](https://wenproducts.com/collections/power-tools) | 1 | 0 | 1 | 1/1 matched |
| [Factory Direct Supply](https://factorydirectsupply.com/collections/power-tools) | 3 | 0 | 8 | 3/3 matched |
| [Grizzly Industrial](https://www.grizzly.com/outlet-specials/shop-all) | 22 | 2 | 27 | 3/3 matched |

The 23 sampled offers matched merchant price, reference, identity, selected options/SKU and stock. This is an admission sample, not a new population accuracy claim or the required release-wide audit. Contender's additional HTML-page request hit HTTP429 after its variant audit passed. Harvey's first two independent audits hit HTTP429; the later fresh-snapshot audit succeeded. Earlier failures remain documented in the receipt. Local source health is ready at 7/7 for each catalog, which measures fresh complete ingestion, not checkout validation.

## What changed

- Reused Fresh Powder's shared `RetailerConfig`, Shopify parser, paced retries, currency checks, bounded complete pagination, exact-offer validation and atomic source snapshots.
- Added `scripts/probe_sources.py`: explicit candidate manifest → isolated snapshot + admission receipt. It refuses an existing output directory and never enables sources automatically.
- Added a category-independent Grizzly adapter consumed by common refresh and merchant auditing. Public JSON-LD must provide one exact SKU URL, USD sale and strikethrough prices, and new/in-stock evidence. Pagination validates the requested page and terminal page; the catalog CLI is capped at 30 pages. Shopify's exact variant rule remains intact.
- Retained Shopify tags for shipping/condition exclusions. ERIK’S global shipping-block tag is excluded; a regional NYC restriction is not incorrectly treated as no US shipping.
- Recognized observed Hardtail/Full Suspension bike types and plain frame taxonomies; excluded display/demo inventory. Cycling size discovery still uses frame-size dimensions.
- Excluded demonstrated tool false positives: cutters, knives, drill guides, stops, switches, stands, books, casters, storage cabinets and repair kits. Kept real machines bundled with fences or straight knives. A title saying Recon overrides misleading structured NewCondition metadata. Handheld planers and industrial sanders are classified appropriately.
- Persisted source category alongside normalized classifications to make future source reviews easier.

## Held candidates and remaining gaps

- Max Warehouse: 21 qualifying listings but no ≥40% discounts; independent sample hit HTTP429. Not enabled.
- Sports Basement: sample bike explicitly unavailable for shipping. Not enabled.
- Infinity Tools: apparent expensive-machine results were accessories, cutters or knives. Not enabled.
- Coastal Tool, MaxTool and Factory Authorized Outlet: targeted feeds completed but contained no usable discounted variants. No reference price was invented from marketing copy or a coupon.
- Colorado Cyclist: candidate collection returned HTTP404. Several other retailer homepages returned access errors; a homepage failure alone does not establish a permanent source outage.

Tools remains materially weaker in deep-discount supply: five new stores add 38 eligible listings, only two at least 40% off. Retailer breadth has improved, but this does not close the market coverage gap or prove superiority. Prioritize lawful public feeds or retailer partnerships for the missing large tool sellers; keep used/blemished and local-only promotions outside the current new/shippable comparison scope.

## Verification and review

Final validation: **351 offline tests passed**; scoped Ruff and `git diff --check` passed. Run `python scripts/check.py -q` to reproduce the isolated suite. Regression coverage includes feed tags, source scope, exact-SKU identity, currency, stock, condition, price/reference pairing, pagination mismatch/truncation retention, independent product auditing and preservation of probe evidence. Local preview `/healthz`, source lists and storefronts were checked. Standalone packaging uses only configured source snapshots and preserves observation dates.

See the [machine-readable receipt](../../benchmarks/2026-11-02-source-expansion.json). Local previews: [Big Ring](http://127.0.0.1:8766/) and [Bench Drop](http://127.0.0.1:8767/). Public release remains separate and requires a fresh successful release-wide merchant audit; this task did not deploy.
