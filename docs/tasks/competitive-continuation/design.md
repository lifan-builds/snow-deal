# Change boundary

The competitive matrix currently retains obsolete own-inventory counts and lacks comparable current competitor cohorts. The evidence belongs in dated benchmark reports and reusable read-only auditing tools, not product ingestion: never ingest competitor inventory into our storefront as merchant data.

Expected edits: docs/COMPETITIVE-BENCHMARK.md and a new dated matrix/receipt; scripts/audit_catalog.py or common benchmark helpers only if measurements need correction; regression tests for actual audit bugs; task-local public HTML evidence and probes. Reuse common query, exact selected-offer validation and existing merchant auditing. Do not alter the ten metric targets, infer unavailable merchant facts, fabricate history or compare localhost speed against production. Public read-only research is authorized; publication remains a separate scoped release action.

Scope may extend to demonstrated retailer adapters or product fixes under the user's broad improvement goal; record concrete evidence and affected paths before implementation. Preserve unrelated dirty work.

## Demonstrated tool recall gap

HardHat's public deal data includes powered jigsaws, oscillating tools and cordless ratchet kits. The shared tools catalog currently misses the first two explicit tool names and lacks powered-ratchet recognition. This is a product recall issue, not a reason to exclude competitors' offers from the benchmark. Extend `catalogs/tools/src/tool_deals/catalog.py` narrowly for observed equipment names and powered ratchets, retain accessory and condition exclusions, and cover positive and consumable/manual-tool negatives in `catalogs/tools/tests/test_tools.py`. Refresh the affected configured Shopify tools feeds into explicit task-owned snapshots, review newly admitted products and merchant samples, then update local previews and benchmark evidence. Keep the competitor payload separate from our merchant inventory.

## Demonstrated snow render delay

Three cold production mobile runs measured Fresh Powder median LCP at 1712 ms, behind Powder Deals (1252 ms) and Ski Finder (992 ms). A separate browser trace found the first stylesheet beginning around 1108 ms despite navigation TTFB around 236 ms; Google Fonts CSS was then discovered through a nested CSS import around 1352 ms. The base template places the critical stylesheet after potentially large structured-data blocks.

Move the existing styles/font discovery into the early HTML head and replace the nested font import with a parallel head link. Keep the same fonts, layout and structured metadata. Expected files: snow base template, field-guide.css and a focused rendering-order regression assertion. Validate existing snow routes plus a paired controlled browser comparison using captured public content, then keep production performance unverified until publication. This is an implementation fix for measured M10 weakness, not a claim that local speed beats production.

## Demonstrated snow condition gap

The public snow cohort contains two explicitly blemished products. Align snow with the existing cycling/tools new-condition cohort by excluding explicit blem/blemished evidence in names, product types and product URL paths. Reuse `exclusion_reason`, so ingestion and downloaded-snapshot repair share the rule; preserve historical prices and timestamps. Add regression coverage for ingestion and snapshot repair. A bare `Demo` word is not sufficient: evo describes the Marker Kingpin 10 Demo as an adjustable binding design, not used condition. Keep that listing and document this distinction in the benchmark contract. This is a cohort eligibility rule, not a claim that cosmetic blemishes affect performance.

## Demonstrated mislabeled frame-size options

Pro Bike Supply's live Yeti product endpoint labels colors as `Size` and sizes as `Color`. Option-name selection alone therefore admits Turquoise, Cobalt and Raw Carbon as frame-size facets. Add an opt-in catalog-owned size-value pattern alongside the existing size-option names, applied by the common Shopify parser. Cycling accepts recognizable frame-size forms and leaves unrecognized values unknown; preserve the full raw options and exact destination, and never infer a size from an option explicitly labeled Color. Snow/tools keep their existing behavior. Test a real swapped-label shape and valid size forms, refresh the affected retailer, then rebuild and verify the explicit local package.
