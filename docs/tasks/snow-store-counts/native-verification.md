# Native browser verification — 6 November 2026 UTC

Verified the corrected worktree on loopback port 8778 with the explicit task-owned public candidate, opened read-only (SHA256 `6f6f76ffff004c5be6fe35764bec6e7eb156c0637ead28d98144892a41ee15fa`). This is a local UI verification, not production or a new merchant-stock observation.

The first attempt exposed an actual browser defect missed by HTTP tests: inserting option children through htmx OOB innerHTML left Circle's selected attribute but changed the live value to the final Boardom option. Replacing the whole select fixed it. Repeated the sequence after the correction:

- Initial Circle equipment view: dropdown and results both 53.
- Include clothing and submit: both 111; actual selected value remains Circle.
- Exact XL and submit: both 9; subsequent retailer selection Boardom yields 15 and retains Boardom.
- Return to Circle and clear size: both 111. Load more appends all 111 cards, removes the next-page link and keeps the Circle selection/count unchanged.
- Keyboard ArrowUp/Enter selects Freeride Boardshop: label/results both 43 and select retains focus after replacement. Tab then moves to the currency control.
- Unknown retailer remains selected at zero on initial load and after an XL htmx submission.

The prepared production card verifier also passes against this local candidate: 53 equipment, 111 all-items across two pages, 9 XL, and zero unknown-size cards; every rendered selected price/reference/options/stock/variant/link matches the database. This does not substitute for the final production check.

Preview limitation: startup was deliberately disabled and the dummy local auth database had no events table, so background analytics POSTs returned 500. Catalog/filter GETs and the checks above succeeded. This is not a clean-console claim; production analytics was outside this local count test.

After rebasing onto the independently reviewed runtime release `b9cfa3f`, the combined safe offline suite passes **1521 tests** with the same eight warnings.
