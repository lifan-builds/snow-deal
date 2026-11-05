# Keep complete snow snapshots deployable

The November 5 scheduled snow deployment and PR23 preview fail LAMBDA_SIZE_EXCEEDED: 225.49 MB exceeds 225 MB after optimization. The newly downloaded public DB compacts to 147,640,320 bytes but continued real observation growth exhausts prior index-compaction savings. Restore deployability with material size headroom while preserving every current/historical row, selected offer and freshness timestamp. Do not delete history, change source admission, increase service plan or inspect auth data.

Bundle the already validated snapshot compressed; materialize an exact verified local copy before the server imports database defaults. Runtime must not download, migrate or change snapshot contents. Explicit DATABASE_PATH and ordinary local development remain compatible. Fail closed on truncated/invalid compressed content; concurrent initialization must never expose partial SQLite data. Preserve skip-download source bytes.

Acceptance: meaningful byte/history/health and failure/concurrency regressions, full offline suite, independent review, real public snapshot round-trip with exact SHA and size evidence, successful Vercel preview/production and live snapshot verification. This necessary deployment repair uses standing approval. Tools PR23 remains separately preserved pending the repaired deployment gate.
