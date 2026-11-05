# Local implementation and review handoff — 5 November 2026 UTC

The build now writes deterministic gzip plus a versioned manifest containing the exact original byte count and SHA256 of the already prepared public snapshot. The source database is retained unchanged, including the skip-download branch. Root app startup resolves the compressed snapshot before importing aggregator.web.app, so database-module defaults and route consumers bind the verified runtime path. Vercel explicitly includes the two compressed artifacts and excludes the uncompressed database.

The stdlib-only helper is catalogs/fresh-powder/src/aggregator/bundled_snapshot.py. Its interfaces are write_snapshot_bundle(source), materialize_snapshot_bundle(archive, manifest, cache_dir=...), and configure_runtime_snapshot(root). Packaging writes atomic deterministic files. Runtime validates the manifest, streams decompression with a declared-size bound, checks the complete original SHA256/size, and atomically publishes a digest-named read-only cache file. A POSIX per-digest advisory lock with a cache recheck serializes extraction, avoiding multiple large temporary snapshots during concurrent cold starts. Valid existing cached bytes are rehashed before reuse; corrupt caches are rebuilt. Failure temporaries are cleaned and an earlier snapshot is retained. No runtime download, SQL operation or migration is performed by the helper.

An explicit DATABASE_PATH wins unchanged. Ordinary uncompressed local development remains available; a Vercel runtime missing or failing bundle validation stops before database defaults bind. The helper does not inspect authentication or deployment state.

## Verification

The two initial regressions failed before implementation: build main did not emit compressed artifacts, and a fresh root-entrypoint process could not bind/use the compressed-only snapshot. Both now pass. The subprocess regression uses a scrubbed environment, fixture-only database, disabled lifespan and an unused auth path; it checks the actual DB default, selected query count, exact source SHA and real health response. No auth database is created.

Twenty new snapshot cases pass, covering deterministic bytes, complete deal/offer/history preservation, skip-download source preservation, verified cache reuse, same-size corrupt cache rebuilding, truncated/non-gzip/overlong/wrong-hash archives, malformed manifests, concurrent initialization, explicit paths, local fallback, missing deployment artifacts and compression failure retention. Six synchronized cold initializers perform exactly one decompression/publication with one temporary DB. The existing layout tests also pass.

Full offline suite: 774 passed with eight existing warning emissions. New helper, entrypoint and snapshot tests pass scoped Ruff; scripts/vercel_build.py retains its single pre-existing BLE001 finding at the build command's top-level error-reporting boundary. Changed Python compiles and scoped/full whitespace checks pass. No type-checker is configured.

The independent reviewer now owns code/test/config corrective edits. Root owns the explicitly downloaded real snapshot round-trip, bundle headroom measurement, preview/production gates and publication. This implementer used temporary fixtures only and performed no network, commit or push actions. Tools PR23 remains separate.
