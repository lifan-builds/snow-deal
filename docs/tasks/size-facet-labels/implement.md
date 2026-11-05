# Implementation and verification

1. Use Trellis implement agent to add regressions and the smallest shared query/web change. Read AGENTS.md, docs/METHODOLOGY.md and relevant docs/project-guidance contracts.
2. Check representative stability, case/whitespace/known aliases, numeric and compound sizes, only-stock/fresh membership, incoming legacy aliases and unknown selection. Show exact selected offers/ranking/counts/pagination unchanged.
3. Root replays the latest public cycling/tools artifact snapshots and records before/after facet counts plus unchanged card populations for all existing size groups. Keep data timestamps intact.
4. Independent Trellis check agent reviews the full diff, fixes findings, runs all offline checks and scoped Ruff.
5. Commit/publish under standing approval, wait for CI and preview checks, merge, package/deploy existing audited fresh snapshots to existing cycling/tools projects. Fresh full refresh is unnecessary if exact prior artifacts remain within 24 hours and their fingerprints/history are preserved; otherwise run the normal audited refresh. Verify both live fingerprints and legacy/compound/unknown size route behavior, record receipt. No new retailer, paid plan, secrets or account changes.
