# Execution

1. Preserve original/model-sort/child-category failures and completed category receipts.
2. Implement the dedicated listing/detail parser and exact destination validation; test the stock, identity, USD, current/reference and pagination boundaries with sanitized public fixtures.
3. Wire the candidate parser into existing ingestion/auditing, leaving the production source disabled.
4. Traverse all seven categories through the production path in an isolated public-data snapshot. Audit every eligible offer if fewer than thirty; otherwise use top ten plus twenty seeded offers. Validate canonical destinations and freight disclosure in the normal storefront without cart actions.
5. Enable only after complete candidate and merchant evidence. Run offline checks and CI, publish under standing approval, then run a fresh tools refresh with history restored and verify the exact public hash and filtered cards.
6. Retain incomplete categories as expansion gaps. Roll back source configuration if publication evidence fails; never publish partial refreshes or relabel historical data as fresh.

Status: parser and regression tests completed; admission stopped by the live shipping restriction. No production source entry, activation or new-stock claim. Keep the unsupported categories and retailer-wide shipping gap open.
