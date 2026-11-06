# Implementation

1. Implement agent reads contracts/research, adds bounded source predicate before offer construction and independent audit guard. Add regressions for actual high-reference and false-stock examples, all-generated rows, surviving base identity, source isolation, query size/count/ranking and old audit rejection. Update parser contract and mirror. Run focused checks.
2. Root captures current full Contender feed, replays exact before/after, reviews every changed offer and refreshes only that source in a restored task-owned snapshot. Verify historical/other-source preservation and audit all affected survivors plus standard sample.
3. Independent check agent reviews final scope and runs full offline checks. Build clean package excluding inactive Circle, verify routes/history and precise offer destinations.
4. Publish scoped PR; wait CI/preview; merge. Upload only validated cycling snapshot and deploy exact clean merged runtime to existing Big Ring. Verify snapshot digest, production fingerprint and generated-size absence. Record limitations and receipts. Roll back matching baseline/runtime if verification fails.
