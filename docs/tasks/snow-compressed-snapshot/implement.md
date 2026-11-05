# Execution

1. Read existing build, app startup and read-only database contracts; add failing byte-roundtrip/history/startup/explicit-path/corruption/concurrency tests.
2. Implement the narrow build compression and pre-import runtime materialization boundary; preserve skip-download bytes and existing compaction semantics.
3. Run affected checks, full offline suite, scoped lint; independent review follows. Record actual outcomes.
4. Root checks the explicitly downloaded current public snapshot round-trip and bundle headroom, publishes this repair separately, verifies Vercel production and the pending tools PR gate, then resumes tools rollout. Standing approval covers this repair. No account/config/paid-service action is needed.
