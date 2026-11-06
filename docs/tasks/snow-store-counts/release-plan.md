# Retailer count release

After the Circle data rollout is reconciled, publish this reviewed change under the user's standing authorization. Merge after CI/preview checks; let the existing FreshPowder deployment consume the current public snapshot. Do not dispatch another merchant refresh for a presentation-only change.

Independent review passes 1469 safe tests and current CI lint/syntax checks. Native verification found and corrected the OOB selection drift; final browser checks are in native-verification.md. Verify production counts against the downloaded current snapshot with clothing and exact-size filters; follow at least one htmx filter update and ensure the live selected retailer stays correct. Confirm source health and the two other catalog fingerprints remain unchanged.

Rollback by reverting the presentation/query-count release. No snapshot/history rollback is required because this release does not mutate data. Source health retains its existing operational ingestion count.
