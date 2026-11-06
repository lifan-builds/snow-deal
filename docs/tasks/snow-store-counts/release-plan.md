# Retailer count release

After the Circle data rollout is reconciled, publish this reviewed change under the user's standing authorization. Merge after CI/preview checks; let the existing FreshPowder deployment consume the current public snapshot. Do not dispatch another merchant refresh for a presentation-only change.

Independent review passes 1469 safe tests and current CI lint/syntax checks. Native verification found and corrected the OOB selection drift; final browser checks are in native-verification.md. Verify production counts against the downloaded current snapshot with clothing and exact-size filters; follow at least one htmx filter update and ensure the live selected retailer stays correct. Confirm source health and the two other catalog fingerprints remain unchanged.

Rollback by reverting the presentation/query-count release. No snapshot/history rollback is required because this release does not mutate data. Source health retains its existing operational ingestion count.

## Production receipt

[PR #49](https://github.com/lifan-builds/snow-deal/pull/49) merged as `28fe5bb` at 07:00:20 UTC on 6 November 2026. Final automatic offline CI and preview passed; production deployment succeeded. Ten initial/fragment checks match every retailer label to the byte-verified public snapshot across equipment, all-items, XL, deep CAD and unknown-retailer scopes. Native production filtering preserves Circle through 9 XL → 111 all-items → 53 equipment results. All three health bodies remain unchanged. No merchant refresh or data upload was performed for this release. See `research/production-verification.json`.

The release also fixes the discovered CI trigger gap by adding `catalogs/fresh-powder/**` to the existing pull-request paths; jobs, commands and permissions are unchanged. Independent review and final automatic CI confirm the correction.
