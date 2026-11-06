# Independent final review

Reviewed the full change against the PRD, design, implementation plan, snow query/parser contracts, web/deployment contract and safe verification guidance. The task has no `check.jsonl`; the listed task artifacts and applicable spec files were loaded directly. The frontend/backend spec indexes are templates, so the actual deal contracts and mirrored project guidance supplied the project rules.

The grouped count uses the existing effective-offer selection, eligibility clauses and joins; it ignores only the retailer filter and omits pagination. Initial and normal filter responses pass the same filters and use escaped shared options. Load-more bypasses the facet query and option update. Operational store health remains separate. The query and HTTP regressions cover the prior inflated label, exact variant/stock selection, clothing, other filters, excluded/stale/future rows, unknown selected values, grouped-query count and fragment behavior.

## Finding fixed

The parent's native browser check found selection drift during the innerHTML out-of-band option update: Circle's selected attribute remained present, but the live select value moved to Boardom. The static HTTP tests did not catch this browser state. With the parent's approval, the response now replaces the whole select through outerHTML, preserving its id/name and rendering the requested selected option in a complete control. It must not carry the old hidden wrapper attribute. The HTTP regression checks the complete visible replacement, selected known/unknown values and escaped unknown text. Both mirrored contracts now require a native check of the live value and subsequent request.

Verification performed independently:

- Safe full offline suite: **1469 passed**, with eight existing warnings.
- Exact repository CI Ruff scope plus the new store-count test: passed.
- Touched legacy snow modules: 12 existing Ruff findings remain, with zero introduced findings, verified against `HEAD` using the same paths and configuration. The route-test file has one fewer import-order finding than the baseline.
- Shared catalog and snow field-guide JavaScript syntax, affected Python syntax and `git diff --check`: passed.
- Type checking: no type checker is configured in the project or CI.

No operational data, credentials, merchant endpoints, deployment state, commits or publication were accessed or changed. Native browser re-verification of the outerHTML correction and release verification remain with the parent session; this review does not claim those outcomes.
