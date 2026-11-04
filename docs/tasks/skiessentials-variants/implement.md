# Execution and release

1. Reconcile probe process 91868 and `full-feed/report.json`; do not rerun a live or complete traversal. Preserve earlier page/product evidence.
2. Review full-feed counts, option names, bundle/condition tags and online-price/currency coverage. Verify additional boots, boards and binding option destinations through normal storefront selections.
3. Implement the dedicated parser and fixtures. Cover mixed prices by SKU, sold-out/unknown/conflicting stock, wrong currency, malformed metadata, bundles, missing/unsafe destinations, page count changes/repeats/caps, and stable history identity.
4. Run candidate ingestion without changing production. Reconcile previous listing inventory; explain removed/changed offers. Audit top ten plus twenty seeded offers through independent product pages within 15 minutes. No small-sample population-accuracy claim.
5. Run offline tests, exact CI lint and source contracts. Enable only after complete evidence. Publish under standing approval and use fresh audited refreshes with preserved history. Verify exact offers on production, including unavailable 172 cm exclusion and the 178 cm destination.
6. Roll back code to the prior parser and retain the last verified snapshot if a gate fails. Do not relabel old data as fresh.

Parallel release work remains authoritative: corrected cycling/tools workflow 41774045047 is running; inspect its final artifacts and exact production hashes. Earlier tools-only job 41773486321 succeeded with snapshot cac9476de337db1ecdb9880d764c84e80f98f0084c6a3cea03f0ecc68eccb5c1; cycling failed before scraping and was not published.

## Verified implementation checkpoint

Probe 91868 and candidate 19490 both completed successfully. The independent sample passed 30/30 in 80 seconds; each exact offer also matches the later completed candidate. Reconciliation: 906 prior listings → 482 exact eligible products; 476 retained URLs, six additions, 424 configurable bundles excluded, six without a supported discounted available variant. One retained product changes price after exact-variant selection. No source URLs disappeared from the complete feed. The 605-test suite and exact CI lint pass.

Corrected catalog workflow 41774045047 completed successfully for both catalogs. Big Ring has 19/19 fresh sources and exact hash 3a19461553893c7f9b3314ffc606d31e5f21d281a9202eca44dd6352cb5da1a6; Bench Drop has 10/10 and f26f493bc32eb16ba870a124a38a3401258c78b139e63792807cd21822df8bc2. Both passed 30/30 merchant checks. See the dated rollout receipt for history and source details.
