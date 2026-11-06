# Circle routing integration review — 6 November 2026 UTC

Code review passes for the separate three-file integration patch SHA256 `c41ae877371168f906ab4c7b06b33c6bf5b6d4e0d9b076229db65f500391b4d8`. This receipt does not admit the source or authorize bypassing current capture/audit gates.

## Findings

No actionable code finding. The canonical www domain agrees with the parser's native product/evidence destinations. The configured Circle source selects the shared parser through the HTTP branch of `scrape_all`; the old browser extractor stays available but is not a fallback for this configuration. The shared fetcher still enforces source-domain detail/evidence requests, bounded traversal, duplicate-page checks and incomplete outcomes. Parser/variant/category behavior is unchanged from the separately reviewed parser SHA256 `08069d99db46af8aee4c467093bc02aa55ffe46ca041e5e365a0ef477f825014`.

The offline integration tests use the actual configured source and routing, with factual helmet HTML/AJAX and an explicitly synthetic singleton collection. They verify the exact CAD price/reference, size/options, stock, image, variant ID and selected purchase destination. They fail on browser routing and verify that contradictory canonical product identity produces no deal and a parse-error outcome. These are meaningful boundary tests; they do not claim a live complete source or variant checkout validation.

Independently inspected all 129 staged release paths and scanned their contents for credential signatures. No ignored state/database/credential paths or secret signatures were found. Verified each of the 14 root fixture edits against the isolated bytes and cleanup receipt: the only difference is removal of the duplicate final newline. No runtime/fixture edit was made by this reviewer.

## Verification

- Isolated configured integration/original Circle/browser-configuration checks: **102 passed**.
- Root Circle parser/options/structure/age checks after fixture cleanup: **291 passed**.
- Exact repository CI lint scope plus affected Circle parser/tests: **pass**. New integration test Ruff and affected Python compilation: **pass**. JavaScript syntax and staged whitespace: **pass**.
- No type checker is configured. The implementer's retained full isolated suite reports **1,453 passed, eight existing warnings**; this review reran the affected focused boundaries instead of duplicating that full run.

## Remaining rollout evidence and documentation

Current final-parser replay, source eligibility, timed independent selected-merchant audit, activation, CI and production/history verification remain root-owned and pending. Preserve the current 406-family collection finding separately from the dated 405-family replay; neither is published inventory. After current replay/audit, update release-plan/result counts and append a current rollout summary with exact evidence. In implementation-status, the older paragraph about reviewer ownership and patch regeneration is superseded by the root integration checkpoint; label it as a historical checkpoint or add an explicit superseded note. Preserve dated capture and failed-run receipts. No new competitive lead is established by this review.

## Follow-up: actual displayed-card sampling

Read-only selection review passes for task-owned `audit-displayed.py`, SHA256 `76e194d220574f24b53126f4f043308d66cce8c96f35464b6c02d954b2636ab1`. It reads the explicit candidate database through the real `query_deals` selection and uses each displayed variant key to require exactly one matching current raw offer. Purchase URL, options, current/reference prices and stock must equal the displayed result. Every card must be CAD and confirmed in stock. The explicit 500-row cap exceeds the known 115-row ingested population; the separately verified persisted exclusions account for the 111 displayed rows.

Independently recomputed sampling from the retained public card/selection JSON without opening a database, running the audit script or making merchant requests: 111 unique listings remain in descending percentage order; fixed top10 plus seed20261102 random20 produces30; all25 source-local CAD500-reference/40percent selected listings are added. The deduplicated union is **49** exact selected offers and equals the saved selection byte-for-value. The source-raw audit's51 is a separate population/result, not this displayed-card sample. Selection JSON SHA256 is `91bd07e2a7f92cc40216ba98cd4ecc8d3e866872b40c0c08ab79f8a1903889fe`.

No sampling/selection mistake found. The wrapper delegates to the unchanged independent selected-HTML verifier and timing/HTTP gates; merchant outcomes still belong to the active audit receipt. Scope is the actual all-items view (`include_clothing=True`) with persisted source eligibility. It does not separately establish the default equipment-only top10 sample, arbitrary size-filter accuracy, checkout, historical selling prices or comparative M3. Root reports the current raw capture complete at406families/1047offers/36pages/0errors and the earlier raw-source audit51/51; those run outcomes were not re-executed in this scoped review.

Root assembly verification:1453full tests pass with8existing warnings. Root-path Ruff required one import-order normalization in the new integration test; fixed mechanically, then2integration tests and the full configured lint scope pass. Final staged whitespace passes. No parser or offer behavior changed.
