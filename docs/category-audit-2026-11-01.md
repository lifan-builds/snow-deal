# Catalog category audit — November 1, 2026 (Pacific)

All **13,969 current listings from 30 retailers** were reclassified. Fresh retailer taxonomy or individually reviewed product-family evidence matched **8,825** listings by exact URL and stored title. **1,266 category values changed** relative to the raw public snapshot, including rows moved to an exclusion status. **353 current listings are excluded**: 77 children's items and 276 non-snow, casual, or otherwise out-of-scope items. Those counts overlap; do not add them together.

There are **10 unresolved listings** and **5 generic boots** without sufficient evidence for a subtype. They remain outside the default equipment feed. The audit is not a claim that every item was manually examined or that retailer metadata is infallible.

## Method and evidence

- Started from public release `latest-data/deals.db`, updated 2026-11-01 23:28:14 UTC, SHA-256 `f527b9b7776746566fcb5613be97ee66eaf37ac15543dd201d9d62c0339a18f3`.
- Evaluated every current record against explicit product nouns, category metadata, bundle structure, exclusion rules and known model names; reviewed category transitions and title/type conflicts.
- Retrieved 8,668 exact product matches across 20 Shopify retailers and 137 across Sacred Ride's specific winter collections. Additional detail/manufacturer checks bring the final match count to 8,825. A further 90 product-detail requests were attempted; 32 Peter Glenn requests failed, and some Backcountry pages supplied no usable description. Failed or empty responses were not treated as evidence.
- Decoded readable Shopify breadcrumb and `Gear:` tags instead of treating internal codes as category names. Preserved meaningful product types for future refreshes. Metadata is reused only for an unchanged URL and title; a renamed listing loses the prior type.
- Reclassified all historical rows as well: 1,644 category/exclusion changes overall. Rebuilt affected model-review associations. The offline audit asserts identical prices, discounts, original check times, first-seen values, URLs, IDs, inventory sizes and complete price history. Length ranges and brands may change when supported by classification/retailer evidence.
- Re-downloaded the release before publication and verified it still matched the starting hash, preventing an overwrite of intervening price updates.

Full row-level reports and the metadata needed to reproduce the classifications are in [the audit archive](https://github.com/lifan-builds/snow-deal-data/releases/download/latest-data/category-audit-2026-11-01.zip). The archive contains public product data only.

## Important corrections

- Ski + binding + boot packages belong to skis; snowboard packages belong to snowboards. Bindings described as fitting particular skis remain bindings. “Ski only — binding not included” remains skis.
- Step On is not automatically a binding: retailer boot taxonomy resolves compatible snowboard boots correctly.
- Boot-cut pants, base layers, balaclavas, bags, boot liners, replacement lenses and spare parts stay out of equipment categories.
- Standalone replacement lenses are accessories; whole goggles with a bonus lens remain goggles. Explicit helmet/MIPS titles override incorrect retailer goggle types.
- Winter walking boots have their own category and stay opt-in. Manufacturer names alone no longer force equipment classifications.
- Children's and non-snow exclusions apply to searches, category counts, brand filters and comparison pages, including the clothing/accessory opt-in view.

Examples of primary evidence used for ambiguous model families:

- [Union Reset Pro snowboard boot](https://unionbindingcompany.com/products/union-reset-pro-mens-snowboard-boot-2027)
- [Scott Celeste/Cosmos ski boots](https://www.scott-sports.com/au/en/en/products/ski-equipment-mw-boots)
- [K2 Marauder splitboard package](https://k2snow.com/en-us/p/marauder-unisex-splitboard-package-b2302002)
- [Helly Hansen Garibaldi V3 winter boots](https://www.hellyhansen.com/en_us/garibaldi-v3-11422)
- [BCA BC Link radios](https://backcountryaccess.com/en-us/c/bc-link-radios/)
- [Yakima FreshTrack ski carrier](https://yakima.com/products/freshtrack-6)
- [Dakine Banked Slalom tuning kit](https://ce.dakine.com/collections/bike-gloves-backpacks/products/banked-slalom-race-kit)

[Flaxta’s decorative helmet top](https://www.backcountry.com/flaxta-deep-space-hardshell-top-helmet) is an accessory, even though its retailer places it in a helmet collection.

Product-family evidence establishes category only; it does not verify an older listing's price, model year or availability.

## Retailer coverage

“Changed” counts category changes; exclusions can overlap. Metadata means a successful exact-title match, not every product detail being current.

| Retailer | Audited | Metadata | Changed | Excluded | Unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alpine Shop VT | 116 | 116 | 0 | 0 | 0 |
| Aspen Ski and Board | 834 | 834 | 97 | 11 | 0 |
| Backcountry | 1559 | 6 | 179 | 14 | 4 |
| Blauer Board Shop | 856 | 855 | 44 | 35 | 0 |
| BlueZone Sports | 64 | 1 | 1 | 0 | 0 |
| Boardom | 146 | 146 | 1 | 0 | 0 |
| Colorado Discount Skis | 249 | 0 | 3 | 0 | 0 |
| Colorado Ski Shop | 377 | 376 | 4 | 2 | 0 |
| Comor Sports | 30 | 30 | 1 | 0 | 0 |
| Corbetts | 62 | 0 | 6 | 1 | 0 |
| Evo | 1055 | 1051 | 1 | 0 | 0 |
| First Stop Board Barn | 192 | 192 | 29 | 18 | 0 |
| Freeride Boardshop | 45 | 45 | 0 | 0 | 0 |
| Fresh Skis | 17 | 17 | 0 | 0 | 0 |
| PRFO | 41 | 41 | 0 | 0 | 0 |
| Peter Glenn | 1976 | 3 | 241 | 88 | 5 |
| Rude Boys | 323 | 323 | 10 | 0 | 0 |
| Sacred Ride | 137 | 137 | 16 | 3 | 0 |
| Ski Depot | 764 | 764 | 114 | 26 | 0 |
| Ski Essentials | 137 | 0 | 10 | 0 | 0 |
| Ski Pro AZ | 1386 | 1386 | 53 | 33 | 0 |
| Skiis & Biikes | 604 | 604 | 72 | 25 | 0 |
| Skirack | 181 | 181 | 46 | 42 | 0 |
| Sports Basement | 1441 | 1441 | 232 | 8 | 0 |
| Steep & Cheap | 206 | 0 | 69 | 0 | 0 |
| The Circle Whistler | 186 | 9 | 12 | 45 | 1 |
| The House | 719 | 1 | 20 | 0 | 0 |
| The Ski Monster | 63 | 63 | 3 | 0 | 0 |
| The Startingate | 77 | 77 | 0 | 0 | 0 |
| UtahSkis | 126 | 126 | 2 | 2 | 0 |

## Remaining uncertain listings

- The Circle Whistler: [Seaside Eyelet Top](https://www.thecirclewhistler.com/seaside-eyelet-top.html)
- Peter Glenn: [Peter Glenn Knit Ruffles Wrap with Real Fox Fur](https://peterglenn.com/peter-glenn-knit-ruffles-wrap-with-real-fox-fur-womens/)
- Peter Glenn: [Outerknown Chroma Blanket Shirt (Men's)](https://peterglenn.com/outerknown-chroma-blanket-shirt-men-s/)
- Backcountry: [Yakima FlushBar - 1 Bar](https://www.backcountry.com/yakima-flushbar)
- Backcountry: [Rhino-Rack Reconn Deck Tower - 1-Pair](https://www.backcountry.com/rhino-rack-reconn-deck-tower-1-pair)
- Backcountry: [ROAM Adventure Co Rugged Mount](https://www.backcountry.com/roam-adventure-co-95l-rugged-mount)
- Backcountry: [ROAM Adventure Co Rugged Case Rigid Mount](https://www.backcountry.com/roam-adventure-co-rugged-case-rigid-mount)
- Peter Glenn: [Goldbergh Astor Top (Women's)](https://peterglenn.com/goldbergh-astor-top-womens/)
- Peter Glenn: [Goldbergh Chandra Top (Women's)](https://peterglenn.com/goldbergh-chandra-top-womens/)
- Peter Glenn: [Peter Glenn Arrow Crystal with Real Fur Pom (Women's)](https://peterglenn.com/peter-glenn-arrow-crystal-with-real-fur-pom-womens/)

The five generic boots are Moon Boot EVX Nylon Mule, Helly Hansen Garibaldi VL, The North Face Snowfuse, Helly Hansen Isolabella 2 Demi and Kamik Sienna 3. They are not promoted as ski or snowboard boots. Their source pages were unavailable for this pass.

## Verification

- 213 offline tests passed, including 49 new evidence and persistence regressions.
- Python compilation and whitespace checks passed. A build-only import failure was fixed by sharing size parsing without importing the scraping package; an isolated regression test covers that dependency boundary.
- Full-snapshot repair is idempotent and preserves all price observations.
- Public category routes and screenshot examples checked against the audited snapshot before publication.

To repeat an offline audit, provide a public snapshot and exact-title metadata:

```sh
python scripts/audit_categories.py --source-db /tmp/source.db --output-db /tmp/new-audited.db --metadata /tmp/metadata.json --report-dir /tmp/category-report
```

The command refuses to overwrite the source or an existing output file. No credentials, authentication database or browser state are needed.
