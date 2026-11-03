# Change boundary

Current gaps: the cycling/tools hero and sidebar consume the first screen; selected filters and independently selected variants need clearer navigation. Retailer data quality is constrained by classification and size handling; shared ingestion needs explicit variant identity checks. Snow needs consistent price evidence and first-screen mobile ergonomics. Competitive leadership is currently unmeasured.

Ownership: common catalog templates/CSS/JS and web/query/storage modules own the shared browsing flow; catalog definitions own classification; common Shopify parser owns option extraction; Fresh Powder card/templates/CSS own snow browsing; scripts and common benchmark helpers own repeatable measurements and leadership gates. Add only changes backed by inspection/tests.

Preserve earlier uncommitted site implementation. Keep snapshots and local browser artifacts in task-owned excluded paths. Only explicitly supplied public-deal snapshots may enter inventory audits. Common code must not import a catalog. Do not change percent-first ranking, production deployment/auth/DNS, original snow plans, or publish claims from missing evidence.

Data flow: retailer offer -> validated variant -> category scope -> eligible filters -> percentage order -> counts/pagination -> card evidence. Benchmark observations carry cohort, method, date, sample size and evidence URL. Unknown is not zero; self-reported claims do not qualify for a measured win; local timing is not production performance.

## Gap-closing continuation

Extend proven retailer coverage in catalog definitions, with category/size validation before enabling a source. Add a separate merchant product-endpoint audit (top ten plus twenty seeded samples, exact variant and raw prices), retaining failures and inconclusive results. Fix history continuity at the workflow boundary: restore prior public snapshot, validate its catalog identity, refresh, then retain the full updated snapshot. Add publication/refresh health evidence without loading local credentials. Strengthen the benchmark's evidence validation rather than weakening its pass criteria. Tests cover the new source exclusions, auditor failures, and restored history. Current work remains on the existing dirty branch; no unrelated reset or repository reorganization.
