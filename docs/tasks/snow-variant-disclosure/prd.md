# Selected snow variant disclosure

Production cards with a selected 180 cm offer linked to its exact merchant variant but incorrectly said “Exact variant not supplied.” The query returned the key, but the display model and its row mapping dropped it.

Acceptance: selected cards disclose the same variant key and option text as their selected price and purchase link, on full and partial pages. Legacy products retain unknown identity. Ranking, stock eligibility and history remain unchanged.

Scope: add one optional field to AggregatedDeal, map the existing selected SQL column, and extend existing query/full-page/partial-page regression checks. No migration or snapshot rewrite.

Validation: all three strengthened regressions failed before the fix; 573 tests pass after it. Exact CI Ruff, JavaScript syntax and whitespace checks pass. Release under standing authorization after green checks; automatic snow code deployment reuses the freshly validated 04:24:46 UTC snapshot. Verify the deployed key against the selected purchase URL and size, plus precise discount ordering. Revert this commit for rollback without changing data history.
