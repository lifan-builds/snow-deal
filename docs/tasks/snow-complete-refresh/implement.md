1. Inspect actual browser/HTTP outcome statuses and the existing persistence gate.
2. Extend the gate, preserving prior collapse behavior and truthful withheld reporting. Test a high-count partial source, failed source without baseline, non-complete collection status with zero errors, unchanged complete source and genuine count collapse.
3. Verify no partial source reaches upsert/history persistence through CLI integration or meaningful temporary-DB test. Run scoped and full offline checks; independent review.
4. Publish tested correction under standing approval and verify a fresh scheduled/targeted receipt. Do not alter earlier public history or claim old observations were repaired.

## Root cause and prevention

The scraper correctly reported pagination failure, but the persistence boundary only guarded count collapse. Tests covered the error report and collapse independently, missing their composition. The new CLI regression follows outcomes through admission into a temporary deal/history database, preventing a healthy partial count from renewing freshness. No retrospective repair is performed: earlier observations remain dated evidence with the recorded source failures.

## Verified rollout

PR #19 merged as `2f471fd`; targeted run `41966876680` completed and production serves `2026-11-05T04:19:09.542689`. The existing House adapter refreshed 690 listings. Public before/after artifacts preserve all 14,533 unselected deal rows, 27,778 unselected offers, 177,163 prior price observations and 226,720 offer observations. Full and partial routes return matching 60-card House pages. See `docs/benchmarks/2026-11-05-snow-completeness-rollout.json`. Failed-source behavior is verified by CLI/database regression; this live run exercised a complete source.
