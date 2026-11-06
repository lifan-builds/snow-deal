# Rollout receipt review — 6 November 2026 UTC

## Findings (fixed)

Root corrected the stale PRD status and described the omitted caveat as the original problem. No runtime or rollout-fact correction was needed from this reviewer.

## Findings (not fixed)

None requiring correction. The separate fixed production sample contains no noted offers: its 30/30 result must not be described as reauditing all 57 pricing caveats after deployment. Those variants were checked in the 87-offer prepublication audit; production note/history rendering and the exact snapshot fingerprint were verified separately. No completed checkout, additional negotiated savings, independently verified historical prices or new competitive lead is established.

## Verification

- All 42 packaged runtime hashes independently match merge commit `7f9ec51bfc5bb75887c6af393cd581b6779b54da`; the reported PR head is a merge parent and inactive Circle is excluded. The retained root receipt records CI's 1,160 passing tests, lint and preview. Runtime tests/CI were not repeated for this documentation review.
- Public asset 715616448 is uploaded. Prepared and canonically restored files are both 10,637,312 bytes with SHA-256 `9b8f8734381ec5978cc711c07601ed1aaa45ce37475b51b39a3df14708c63d04`. The retained restore output and asset receipt record first-attempt success. Packaged logical source rows and all 59 observation rows match the prepared snapshot; physical-byte identity is not inferred for the separately packaged database.
- All 20 other source rows and 58 earlier-day/other-source observations remain exact. Only Contender's 01:32 same-day observation is replaced by its real 02:08 observation, preserving the existing daily policy and total of 59. Current data has 57 notes across 27 products, with other offer facts unchanged. The BMC correction retains the distinct evidence: four unavailable variants present at 01:32, raw product absent at 02:08.
- Deployment output, live-health, semantic and rollout receipts join correctly for READY production deployment `dpl_CFFPZtmmd78vUNy8QzHWt7eQxEKW`. The healthy 21-source logical fingerprint is `5253fbcfe4098f914d7308bcb460104c3b82dc5243fa5543692094a749ef15e1`. Default confirmed-stock/deep counts remain 1,475/203.
- Live evidence covers 13 routes and 279 card comparisons, all 182 selected Contender destinations, 29 distinct noted destinations, the source page and 38 history pages. It records 29 current annotated rows and 86 older rows without backfilled notes. The helper checks selected-card text/links and each dated history note against the package. Recorded native 390px QA checks the exact ordinary Rapha XL price/reference, note beside price/details, current-only history note, absence of document overflow and viewport reset; this reviewer did not repeat the browser inspection.
- Independently recomputed the top-ten plus seeded-twenty production sample from all 1,475 confirmed-stock cards with seed 20261106. All 30 selected-offer dictionaries join exactly to the 30 merchant results, and the 14 recorded display pages are exactly those required. Every factual check passes, with zero mismatch/inconclusive results. The conservative display-check window starts at 02:28:34.737878 UTC; page responses finish at 02:28:35.227407–02:28:42.006926 and the final merchant result at 02:30:52.611107, 137.873229 seconds after the window starts. All results also satisfy their audit window.
- Task/rollout JSON parses, local links resolve and whitespace checks pass. Current notes are not applied to earlier observations. Limitations remain explicit and the existing five strict leads across 260 comparisons are unchanged.

Receipt review passes. All reviewer-owned edits are finished. No network, credentials, operational database, runtime edits, commits or publication actions were used.
