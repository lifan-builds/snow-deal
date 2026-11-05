# Independent manufacturer-filter review

## Scope and findings

Completed the required Phase 2.2 final review across all five common modules, both catalog alias tables, the new regression file, task artifacts, retained primary evidence, public replay and applicable project guidance. The package inventory reports a single repository without configured packages; the backend/frontend spec indexes remain placeholders, so the concrete deal and `docs/project-guidance/` contracts govern this review.

No correctness defect or unresolved code finding was identified. No runtime or test change was necessary.

## Identity and data flow

The existing manufacturer helper rejects fulfillment labels before applying only explicit casefolded aliases. All existing mappings remain intact, keys are unique and every target is idempotent. The 17 cycling groups and three tools groups agree with all 43 retained successful merchant metadata checks. Axiom's manufacturer-site refusal remains documented; the two selling retailers corroborate the exact AR8PROV6 identity. These are manufacturer-label mappings, not product, package or model-year equivalence. S-Works, Specialized Turbo, SCOR, Metabo HPT, unknown labels and retailer-as-brand records remain separate.

Ingestion, requested filters, facet/card display and history comparison share the helper. Canonicalization happens before brand filtering, counts and pagination. Original-brand free-text searches remain available. Known legacy URLs select the canonical form option and generate canonical pagination/filter links; unknown values remain escaped. Existing saved searches still reach the corrected server route without a local-storage migration. Empty-alias query calls retain their previous semantics.

Query and history presentation use projected product dictionaries. Selected offer fields and source rows remain untouched. History retains the exact source, product URL/name, variant ID/options and destination guards while comparing only manufacturer labels through the alias map. Regression tests cover prior-day unknown stock/notices, subsequent canonical ingestion, genuinely different manufacturers and every other exact identity guard. Health receives raw sources rather than display projections; no schema, observation, price, timestamp, transport, ranking or stock rule changes.

## Public-data replay

Independently loaded the specifically authorized public snapshots read-only and compared the final query against the actual HEAD query implementation at the receipt's fixed timestamp. All 9,312 selected-card comparisons across 15 scenarios match, except the intended display brand. Counts, ordering, selected variants and their complete offer fields are unchanged. Both original database SHA values, source input dictionaries and raw health receipts remain unchanged.

Reviewed the root replay helper and receipt: cycling facets change 109 to 89 and tools 50 to 47; 338 alias-union comparisons and 43 form routes pass. The history replay retains prior matching observations for 2,669 current offers across 7,337 returned records. Synthetic negative tests separately prevent cross-manufacturer or other identity joins. Root's standard-package verification retains all 57 cycling and 34 tools observation rows. Packaging and live verification remain separate release gates.

## Verification and limits

- Full offline suite: **928 passed**, eight existing warnings.
- Exact CI Ruff scope plus the new regression file: **passed**.
- Shared catalog JavaScript syntax, changed Python compilation and whitespace checks: **passed**.
- Type checker: not configured.

No network, credential access, operational database, publication, commit or deployment was performed during this review. The explicit task-owned public snapshots were read-only. The 43 retained merchant checks support these exact aliases; they do not establish fresh stock, checkout behavior, historical prices or competitive leadership. Root owns release CI, package/live reconciliation and rollout.
