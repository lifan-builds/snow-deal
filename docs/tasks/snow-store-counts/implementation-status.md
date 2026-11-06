# Implementation result

Implemented in separate worktree `/Users/lfan/.codex/worktrees/snow-store-counts/fresh-powder`, branch `codex/snow-store-counts`, baseline3043f75. No commit or publication.

The concrete HTTP regression failed before the change: a retailer with one visible equipment listing displayed `Evo (3)` because its source batch also contained clothing and an excluded child product. It now displays one for equipment and two with clothing. A grouped mode in the existing deal query shares selected-offer and eligibility clauses, ignores only the retailer facet, and executes one grouped SQL query before pagination. Store health retains its ingestion meaning.

Initial and normal htmx filter responses share retailer options. Following a native-browser finding, the fragment replaces the complete select with the same id/name and requested selected option; an unknown selected value is escaped and visible with zero count. Load-more emits no retailer options. Category/brand facets, ingestion, snapshots/history and ranking are unchanged.

Verification:33focused query/HTTP tests pass;1469full offline tests pass with8existing warnings. Exact repository CI lint plus new test lint, JavaScript syntax, affected Python compilation and whitespace checks pass. The touched older snow DB/routes/test modules have12pre-existing lint findings in total and zero new findings; one pre-existing top import-order finding was normalized because the imports changed. No type checker is configured.

Read-only public candidate reconciliation passes at SHA2566f6f76ffff004c5be6fe35764bec6e7eb156c0637ead28d98144892a41ee15fa:Circle facet counts equal111all items,53equipment,9XL and25CADdeep cohort, matching the visible count query in each case. Operational source count stays115. The grouped query takes0.12–0.25seconds in this single local observation; it is not a comparative latency or production-performance claim. Snapshot bytes remain exact. See research/candidate-reconciliation.json.

Independent review passed the query checks, then incorporated the parent's native-browser selection-drift finding and replaced the innerHTML OOB swap with outerHTML. Native local-browser re-verification of that fix remains with root, followed by a separate release after the Circle rollout is reconciled. No network scrape, merchant request, credential access, operational data mutation, commit, push or deployment was used.
