# Independent tools equipment recall review

Reviewed the complete classifier/test diff, PRD/design/implementation plan, source reassessment, retained package evidence and the affected normalization/query path. Final code is stable for a fresh candidate run. Source configuration, stock/transport rules, request budgets, ranking and history writes are unchanged.

## Findings fixed

- The broad primary `base` exclusion rejected the existing Bosch EVS Fixed-Base Router. Preserve that observed machine descriptor while continuing to reject a router base or a Fixed-Base Router Stand.
- Splitting at included-accessory wording dropped explicit whole-product package facts. Read Bare Tool/Tool Only labels from the complete title, and retain explicit battery-and-charger Kit / numeric Ah Kit descriptions. A Blade Kit or accessory Bundle in the included suffix does not become the primary tool's format. This restores the existing Bosch/Fasteners/Tool Nut bare tools, Milwaukee 5.0Ah Kit and Woodcraft kits.
- Generic primary headings such as Bundle or Tool Set cannot become equipment solely because the retailer category mentions a saw. Accessory-primary, condition, replacement and conflicting pre-existing taxonomy checks remain ahead of equipment classification.
- Singular Consumable taxonomy now receives the same exclusion as Consumables. Explicit singular/plural blade/filter title exclusions remain intact; Blade Right Circular Saw is the observed machine-orientation exception.

Seven added review regressions initially failed before the corresponding fixes. Further baseline coverage locks in the existing Milwaukee kit and the previously accepted named DEWALT hand vacuum. The final tools module has 103 tests; normalized Bundle filtering preserves the exact selected offer price, reference, stock and purchase URL.

## Full baseline and deferred finding

Replayed all 657 product names/types in the explicitly downloaded public tools snapshot. The final classifier preserves every previous category, package and platform label except the intended rejection of OakTree's `MK Morse Advanced Edge Power Reciprocating Saw Blades 9 in. x 18 TPI (25 Pack)`, previously admitted through a singular-blade title regex gap. The retained baseline receipt is `.local/source-expansion/tools-recall-20261105/baseline-replay.json`. This is classification replay, not renewed stock or price evidence.

A proposed new Filters taxonomy exclusion would remove the existing `DEWALT DCV501HB Hand Vacuum` because its retailer type is Filters. The main session explicitly deferred that precedence question pending separate merchant evidence. The new Filters gate was removed; no source/product whitelist or relaxation of pre-existing taxonomy rules was added. Accessory filter titles still fail through the explicit title guards. This conflicting taxonomy is a deferred research finding outside this recall correction.

The unchanged three-feed comparison identified 63 additional Beaver equipment listings, including 11 JET lathes and four Kreg drills beyond the original 48-package research cohort. Their primary titles describe complete equipment. Retained separate merchant checks are dated research: twelve have delayed shipment and must remain unknown stock; they cannot satisfy confirmed-stock filters. The earlier 48/48 matches and supplemental identity/money agreement do not replace fresh complete-source admission or the timed merchant audit.

## Verification and limits

Final full offline suite: **797 passed**, eight existing warning emissions. Scoped tools Ruff, AST parsing and whitespace checks pass. No type-checker is configured. All existing negative cases pass, including accessory-only titles, contradictory existing accessory taxonomy, replacements, consumables, used/open-box stock, ambiguous package heads and the unsupported air-filtration machine.

No network, browser, production database, commit or push action was performed during review. Fresh full candidate traversal, current purchase-panel reconciliation, timed merchant audit, CI and deployed-snapshot verification remain the main session's release gates. No increase in deep-discount counts or competitive lead is claimed by this review.
