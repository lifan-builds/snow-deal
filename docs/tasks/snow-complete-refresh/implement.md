1. Inspect actual browser/HTTP outcome statuses and the existing persistence gate.
2. Extend the gate, preserving prior collapse behavior and truthful withheld reporting. Test a high-count partial source, failed source without baseline, non-complete collection status with zero errors, unchanged complete source and genuine count collapse.
3. Verify no partial source reaches upsert/history persistence through CLI integration or meaningful temporary-DB test. Run scoped and full offline checks; independent review.
4. Publish tested correction under standing approval and verify a fresh scheduled/targeted receipt. Do not alter earlier public history or claim old observations were repaired.

## Root cause and prevention

The scraper correctly reported pagination failure, but the persistence boundary only guarded count collapse. Tests covered the error report and collapse independently, missing their composition. The new CLI regression follows outcomes through admission into a temporary deal/history database, preventing a healthy partial count from renewing freshness. No retrospective repair is performed: earlier observations remain dated evidence with the recorded source failures.
