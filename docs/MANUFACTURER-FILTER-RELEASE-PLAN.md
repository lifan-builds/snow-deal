# Consistent manufacturer filters

Big Ring and Bench Drop currently split one manufacturer across retailer spellings. For example, choosing Santa Cruz hides offers stored as Santa Cruz Bikes or Santa Cruz Bicycles. This release uses explicit, evidence-backed catalog aliases throughout ingestion, current filtering, cards and exact-offer history. It does not merge products or variants.

## Scope and evidence

Seventeen cycling manufacturer groups and three tools groups are documented in `docs/tasks/manufacturer-filters/research/aliases.json`, including primary manufacturer identity pages and 43 successful public merchant metadata checks. Axiom's manufacturer homepage refused access; the two selling retailers independently identify the same AR8PROV6 machine under Axiom and Axiom Precision. No access workaround was attempted. S-Works, Specialized Turbo, SCOR, Metabo HPT and retailer-as-brand entries remain distinct.

Canonical and legacy brand URLs return the same group before counting and pagination. Raw-brand free-text search still works. History compares manufacturer aliases while preserving exact source, product URL/name, variant ID/options and purchase destination. Price, reference, stock, options, ordering and observation times remain intact. The health fingerprint continues to represent raw source rows.

## Validation and rollout

Run the focused regressions, full offline suite, exact CI lint and independent review. Replay both explicitly downloaded current public snapshots read-only: every alias group must equal the union of the original labels, unrestricted selected offers must be identical except for display brand, and existing historical observations must remain reachable. Verify selected form state and canonical pagination parameters.

Under standing approval for comparable releases, publish the reviewed branch, wait for CI and preview checks, then merge. Package the same fresh public snapshots using `scripts/package_catalog.py`, preserving logical source/history rows and timestamps; verify their raw fingerprints before deploying to the existing Big Ring and Bench Drop Vercel projects. No fresh scrape, public database-asset upload, schedule change or freshness restamping is required. Reconcile production and scheduled-run state before deployment so a newer snapshot is never replaced with an older one.

Verify production health, canonical/legacy brand routes, multi-page results, exact offer fields and history against the local packaged app. Record code/merge/deployment IDs and dated receipts. This metadata correction does not establish new inventory, stock accuracy, historical-low or competitive-lead claims. Fresh Powder uses its separate app and requires no deployment for this change.

## Recovery

If code checks fail, do not deploy. If a post-deploy route or fingerprint differs, retain the failed receipt and restore the previous verified deployment through the existing Vercel project. Keep public snapshots and stored historical records untouched. Investigate the discrepancy before retrying. The prior deployments are recorded in the local pre-release inspect receipts and the dated rollout record.

## Verified result

PR #32 merged after 928 passing CI tests and a successful preview. Both production deployments are Ready; 52 filter routes and 25 history pages match the packaged data. All raw fingerprints and 91 observation rows remain intact. See `docs/benchmarks/2026-11-05-manufacturer-filters-rollout.json` for deployment IDs, route results and evidence limits.
