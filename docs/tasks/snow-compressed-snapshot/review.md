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

## Opt-in runner preview follow-up review

Reviewed only the added manual `snow_preview` input/job in `.github/workflows/catalog-check.yml`. Its boolean defaults false; the job requires workflow_dispatch plus that explicit input and successful offline checks. The existing pull-request trigger, read-only repository permissions and complete offline/RA candidate job are unchanged. Deployment secrets are scoped to the opt-in job, with the token limited to its deployment step. The known Fresh Powder project-ID guard runs before deployment. No production/alias/promote command or additional service was introduced.

Made two narrow hardening/clarity edits: explicitly pass `--target=preview`, and set `persist-credentials: false` only on the preview job's checkout. Node 22 and Vercel CLI 65.9.0 remain pinned as proposed. The URL summary accepts only an HTTPS Vercel hostname without credentials, port, extra path, query or fragment; malformed output fails instead of publishing a misleading link.

Offline checks parsed YAML, verified the event/default/dependency/secret scopes and byte-equivalent offline/RA structure, and passed shell plus embedded JavaScript syntax checks. Seven synthetic URL/project-ID cases passed using a local shell function in place of the Vercel command; a final stub also required the explicit preview target and verified checkout isolation. No real CLI deployment, network, workflow dispatch or secret inspection occurred. Python/runtime code is unchanged, so the prior 776-test result remains applicable. The workflow is stable for the main session's commit/CI and reconciled explicit dispatch; provider preview success remains unverified by this offline review.
