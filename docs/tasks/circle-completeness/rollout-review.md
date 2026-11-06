# Production receipt review

Reviewed the Circle production documentation and JSON receipts against the task-owned public-source evidence under `.local/source-expansion/circle-completeness-20261106/production/`. This was an offline evidence-consistency review, not another scrape or live audit. No database, credentials, browser state or network was accessed.

## Findings fixed

The release plan's opening sentence still claimed that publication had not occurred. Replaced it with the verified production status and an explanation that the original scope/gates remain the execution record. No numerical receipt or captured evidence was altered.

## Verified consistency

- Run `42169798783` completed successfully at merged head `3043f75`. The source report has 36 complete collection pages, 406 product/evidence pairs, zero errors, 115 published ingestion rows and 213 exact offers.
- Asset `716152772` is recorded as 206,700,544 bytes with SHA-256 `da8b167a24b8c41b06b04f1617e98816e6467ddd8249115342d44804a97cbf1a`. Provider metadata, preservation receipt and rollout summary agree. Fresh Powder health reports the source report's `06:24:43.262706` UTC check. Big Ring/Bench Drop retain the recorded 21/21 and 13/13 source health and prior fingerprints.
- All 15,250 unselected retailer rows and 27,844 unselected offers are recorded exact; all 217,626 prior price rows and 301,732 prior offer observations are retained. New history deltas are exactly 115 price rows and 213 offer observations. This review checks those preservation receipts, not the underlying database again.
- The live receipt has 53 equipment, 111 all-items across two pages, 9 XL and zero unknown-size cards. Their sum is **173 aggregate card comparisons across overlapping scopes**, not 173 distinct products. Every scope records matching selected price, reference, size/options, stock, link and variant disclosure.
- The retry selection records the actual 111-listing population, fixed top-ten plus seeded-twenty sample and all 25 source-local CAD-reference-at-least-$500/discount-at-least-40% offers. The union contains 49 unique listings; exactly 25 satisfy the stated CAD thresholds. All 49 retry results match the selected records and have independently recorded response paths/check times within **120.171 seconds** of the retry sample, below 15 minutes.
- The earlier audit remains failed: 25 matches, 24 inconclusive results, and 1,098.087 seconds elapsed. The retry has its own sample time, 49 response records and check timestamps; no expired result was combined into the passing run or restamped.
- Published production JSON equals its task-owned source evidence. The live-card receipt intentionally replaces a local database path with the public asset identity; its other fields are identical. The source-quality report's missing-category/image/size counts remain visible rather than being presented as perfect data.
- Five strict leads across 260 comparisons agrees with the existing cycling-reference matrix. The notes correctly preserve the CAD/USD, retailer-reference, unmeasured-competition and saturation limitations. Feed-access research distinguishes provider claims and proposed access from actual authorization, adapter admission or new inventory.

## Remaining findings and checks

No unresolved inconsistency was found in the reviewed Circle receipts. PR #49's separate live facet-count verification is owned by the parent and is outside this review. Workflow-only PR #48's conditional skip remains a future necessary-run observation, not a completed live claim.

JSON identity/arithmetic, audit result/time-window assertions and `git diff --check` pass. No runtime code changed, so an additional full application test run was not necessary for this documentation-only review. No commit or publication was performed by the reviewer.
