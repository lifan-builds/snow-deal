# Implementation status

Boundary: restoration currently verifies SQLite/catalog validity but not whether
downloaded bytes match the selected release metadata. Validate the selected
uploaded asset's positive integer size (excluding bool, bounded by MAX_BYTES)
and strict sha256 digest before destination setup or download. Stream-count and
hash all bytes, then require exact metadata agreement before SQLite is opened.

Owned paths: scripts/restore_catalog.py, common/tests/test_catalog_restore.py,
the web/deployment contract and its Trellis mirror, and this status. No URL,
authentication scope, retry, budget, bootstrap authorization, runtime/source,
schema or deployment change. Other agents' Circle/root edits stay untouched.

Implementation is stable and ready for independent full-scope review. No
public/operational database, credential or network reads by the implementer;
root owns retained/live reproduction, asset verification and publication.

## Implemented

- `scripts/restore_catalog.py` validates release structure and a unique selected
  name. Require exact uploaded state, positive non-bool integer size at most the
  unchanged 100 MiB limit, and `sha256:` plus exactly 64 hexadecimal characters.
  Hex case is accepted; algorithm spelling and whitespace are strict. Invalid
  metadata fails before destination setup or asset request. A well-formed list
  that explicitly lacks the named asset preserves the old bootstrap behavior.
- Hash incrementally while streaming, reject excess expected length/budget
  immediately, then compare final exact length and SHA-256 before any SQLite
  open. Temporary cleanup, read-only SQLite integrity/catalog/source checks and
  atomic destination placement remain. Fixed URL construction, metadata-only
  token scope, metadata redirect refusal, overwrite refusal and no-retry behavior
  are unchanged.
- Append the exact-byte restore contract to both
  `docs/project-guidance/web-auth-and-deployment.md` and its Trellis mirror.
- Expand only `common/tests/test_catalog_restore.py`, using valid synthetic
  temporary snapshots and mocked HTTP. No downloaded/public DB bytes were read
  by the implementer.

## Checks

- Before implementation, the initial 77-case focused run had **64 failed,
  13 passed**. Valid stale-history and valid same-sized changed SQLite files were
  accepted; invalid state/size/digest still downloaded; unverified streams reached
  SQLite. These failures reproduce the behavior gap without live requests.
- Final focused suite: **79 passed**. Coverage includes exact streamed successful
  bytes plus both prior/current history rows; valid stale and equal-length changed
  files in both bootstrap modes; malformed/missing/unsupported metadata before
  setup/download; duplicate named assets; short/excess/wrong-digest streams before
  SQLite and partial-temp cleanup; matching-metadata non-SQLite refusal; wrong
  catalog and overwrite refusal; absent-asset bootstrap; metadata/asset HTTP
  failures; token/redirect isolation and existing metadata redirect/rate limits.
- Scoped Ruff for the restoration script and test file: **passed**.
- `git diff --check`: **passed**.

## Handoff

Root was notified of code stability and focused checks. Independent review/full
offline CI and root-owned read-only live restores of both public assets remain
the next gate. Pinning proves agreement with the metadata read in this invocation,
not that a publisher cannot replace the asset later. An integrity mismatch must
fail explicitly; the caller can invoke restoration again after publication settles.

Only the five assigned paths were edited. Circle untracked work and root PLANS/
research remain untouched. No runtime rendering, sources, ranking, schema,
cloud upload, refresh, deployment, commit or push action was performed.
