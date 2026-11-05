# Local implementation and review handoff — 5 November 2026 UTC

The tools classifier now separates an explicitly included suffix (with, w/, including) from the primary equipment title for accessory rejection and equipment classification. Full-title condition exclusions and retailer accessory taxonomy remain active. The observed Blade Right Circular Saw descriptor is accepted; blade/filter-only titles and plural consumables remain excluded. Explicit fixed Bundle labels appear as Bundle; accessory suffix labels do not imply the complete tool is a Kit or Bundle. No battery contents or platform are inferred.

Changed implementation files are catalogs/tools/src/tool_deals/catalog.py and catalogs/tools/tests/test_tools.py. No sources, parsers, budgets, other catalogs or deployment state changed. No network requests were made by the implementer.

## Regression evidence

Before the correction, all four checked merchant examples failed classification. The initial regression run had nine failures, covering those four examples, two additional complete-tool cases, two overly broad prior admissions and exact bundle normalization/query binding. Follow-up tests demonstrated seven accessory-primary heads newly exposed by suffix trimming (stand, bag, fence, base, guide, case and guard), then verified those remain rejected while a complete saw with a stand and extractor with filter bags remain eligible.

Final independent review passed 103 focused tools tests and the full 797-test offline suite, with eight existing warning emissions. Scoped Ruff and whitespace checks pass. The two pre-existing import-order findings in the owned tools test module were corrected. No type-checker is configured.

## Full retained-feed reconciliation

The complete unchanged capture replay is saved at .local/source-expansion/tools-recall-20261105/implementation-classifier-reconciliation.json. It includes every addition, removal, category/format change and raw per-offer price/reference/availability. Original capture timestamps are preserved; no freshness is renewed. Feed-reported stock is provisional and is not purchase-panel stock evidence.

Initial Beaver replay: 610 parsed products, classification 192 -> 254, with 63 additions, one removal and one format change. Provisional feed stock above the $200 reference floor is 157 -> 219; provisional deep coverage is 15 -> 16. Woodcraft stays 8 -> 8, with one format change; OakTree stays 22 -> 22 with no classification changes. Fifteen additions beyond the separately checked 48-package population are eleven JET lathes with included DRO/taper attachments and four Kreg drills with pocket-hole jigs; their details are in implementation-additional-products.json beside the reconciliation and require separate merchant checks.

Reconciliation exposed a real unintended removal: Bosch EVS Fixed-Base Router w/ Trigger Control was caught by the accessory-head base guard. It also exposed loss of explicit Bare Tool after a descriptive with-suffix and Kit after an explicit battery-and-charger phrase. Independent review fixed these regressions and preserved the existing Milwaukee numeric-Ah Kit. Replaying all 657 stored baseline products now changes only the intended exclusion of a consumable saw-blade pack. The initial raw-feed numbers above are not final admission counts.

Independent review is complete; see review.md. A fresh complete parser candidate, timed merchant evidence and root-controlled publication remain outstanding. PM1250 air filtration stays outside this correction. No production coverage or new >=40% claim follows from these provisional feed numbers.

## Final unchanged-feed replay

The reviewed classifier replay on the same dated raw capture yields Beaver 192 -> 255 accepted products: 63 additions, zero removals and zero label changes among prior products. Woodcraft remains 8/8 and OakTree 22/22 with no changes. See research/final-classifier-reconciliation.json. The separately downloaded 657-product baseline changes only the saw-blade consumable exclusion; no existing equipment category/package/platform changes remain. These are controlled classification comparisons, not refreshed price or stock claims.

## Complete candidate and additional Tool Nut findings

All eleven sources completed with zero refresh errors. The candidate has 515 eligible in-stock listings above the $200 retailer-reference floor, 34 at least 40% off, and six retailers contributing such deep deals. Reapplying the old classifier to the same retained candidate gives 446 eligible in-stock listings: the correction recovers 69 (51 Beaver, 18 Tool Nut), including two Tool Nut Rupes sanders at 46.30% and 46.20% off. This counterfactual cannot reconstruct old-only excluded products; the complete baseline replay separately checks removals. Inventory changes explain why the net change from the older 455-listing snapshot differs from the 69 recovered listings.

All 18 newly admitted Tool Nut purchase-page titles match. Two sanders explicitly say In Stock - Ready to Ship; sixteen lathes say In Stock - Ships from Manufacturer. See research/toolnut-purchase-pages.json. The twelve delayed Beaver offers remain unknown stock; the same model at another retailer must be judged using that retailer's own evidence. Bundle filtering returns 47 in-stock packages in the local preview. Expanded audit passed 95/95 within the 15-minute window, covering the standard 30-offer sample plus every new in-stock offer. All 21 prior history observations are retained exactly; eleven new source observations bring the candidate to 32. See research/candidate-admission.json and research/candidate-merchant-audit.json. CI and production rollout remain pending.

## Reconciled deployment dependency

PR24 repaired the independent snow bundle-size failure, preserving all history. Its production deployment and custom hostname are verified, including eight route/filter combinations and480selected-card observations. Merging that reviewed main branch into this tools branch changes only the shared deployment prerequisite; the combined819-test suite passes. Tools release CI and fresh production catalog rollout remain pending.
