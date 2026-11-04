# Execution

1. Complete storefront, shipping and variant-state research; retain failed merchant-advertised bikes-on-sale 404 and working normal-navigation bikes cohort.
2. Implement/test exact per-variant inventory and destination binding only from observed public page data. Test virtual warehouse, unavailable, missing/ambiguous IDs, prices, currencies and sizes; preserve last successful source on incomplete refresh.
3. Run fresh isolated full candidate; independent fixed top ten plus seeded twenty audit and all deep offers. Audit normal selected-product display without cart actions.
4. Only after gates pass, enable source and run offline checks and CI plus audited deployment with history restoration. Compare real counts, not provisional feed-only numbers.

## Local evidence and runner handoff

The complete detail-aware candidate has 116 qualifying immediate-stock listings and 64 deep deals. All captured HTML/JSON pairs were replayed with the final decoder; only notice text changed, and original observation times were preserved. Two local audits expired during execution pauses (69/76 and 2/76 timely matches, no mismatches). Both are failed gates, retained as evidence. Use the existing check workflow’s opt-in candidate admission on a GitHub runner to obtain a new complete candidate and audit. RA remains disabled until a timely complete audit passes.

Runner admission `41874414409` passed: complete 3-page/144-product/evidence traversal, 116 qualifying in-stock listings, 64 deep listings and 76/76 merchant checks within the audit window. RA is now configured locally. Combined preview preserves all 36 baseline cycling history rows and confirms percentage-first ordering and distinct exact 50s/50cm selections. Production refresh/verification remains required.
