# Independent compressed snapshot review

Reviewed the complete helper, root entrypoint, build integration, Vercel include/exclude configuration, new tests and task/deployment contracts. The packaging representation preserves the prepared database bytes; runtime reconstructs locally without SQL, network or migration work. Entrypoint initialization precedes imports that bind DB_PATH/default arguments. The helper is snow-owned and stdlib-only; no unrelated parser/catalog or history policy change is present. Code is stable for the main session's real-snapshot and deployment gates.

## Findings fixed

1. A killed initializer cannot run the extraction finally block, leaving a potentially large temporary file. Extraction now uses digest-scoped temporary names; the next initializer removes only abandoned temporary files for that digest while holding its exclusive digest lock. A failing-before regression demonstrates cleanup while retaining another digest's temporary file and prior cached database. Normal six-way cold initialization still performs one decompression/publication and creates only one active temporary database.
2. Automatic compressed-only local startup selected an immutable cache path but could leave DEALS_DB_READ_ONLY false, allowing startup to attempt local initialization/migration. Compressed selection now sets the read-only flag before database consumers import. Fresh-process entrypoint tests exercise both local and Vercel modes with the flag initially false; both bind the verified default path, report read-only runtime behavior and serve the fixture health/query result. Explicit DATABASE_PATH and ordinary uncompressed local settings still win unchanged.

## Verification

The final full offline suite passes **776 tests**, with eight existing warning emissions. Twenty-two snapshot cases cover deterministic compression, exact byte/history round trips, byte-preserving skip-download behavior, correct pre-import defaults/health, cache reuse/rebuilding, corrupt/truncated/overlong streams, malformed manifests, failure cleanup, simultaneous cold starts, abandoned extraction cleanup and explicit/local compatibility. These tests use temporary fixtures and a scrubbed subprocess environment; no auth database is created.

Scoped Ruff passes for the helper, entrypoint and snapshot tests. scripts/vercel_build.py retains its single pre-existing BLE001 top-level error-boundary finding; no new lint finding was introduced. Changed Python parses, Vercel JSON parses and whitespace checks pass. No type-checker is configured. No commit, push, network, deployment, operational/auth database or credential-state access occurred during review.

## Remaining release checks and limits

The root's retained public-snapshot evidence records 147,640,320 prepared bytes compressing to 18,230,396 bytes with exact SHA256 equality. Because the helper changed during review, rerun reconstruction using a fresh task-owned cache before publication. Actual function size, artifact inclusion, cold-start behavior and production health still require successful provider preview/production verification; local timings are not deployed latency evidence. Advisory locking targets the project's POSIX macOS/Linux hosts. Other snapshot digests/caches are deliberately retained, rather than broadly deleted. Tools PR23 and its source admission remain separate.
