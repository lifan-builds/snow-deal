# Execution

1. Read existing query/filter/template/testing contracts and find smallest shared SQL construction boundary.
2. Add failing fixture proving115ingested vs111visible-style discrepancy, confirmed variant/size choice and stale/excluded suppression; test current other filters and selected store exclusion. Keep operational counts unchanged.
3. Implement grouped retailer counts and route wiring with a bounded query count. Preserve existing result/count/paging behavior.
4. Run focused and full offline checks using /Users/lfan/Project/fresh-powder/.venv/bin/python scripts/check.py. Run exact repo CI lint plus newly touched tests where applicable; distinguish pre-existing snow lint findings.
5. Independent review, task-owned public candidate read-only reconciliation, local UI. Root publishes only after Circle pipeline outcome is reconciled. No operational DB, credentials, network scraping, account actions or source configuration changes.
