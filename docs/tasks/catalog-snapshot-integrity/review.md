# Independent snapshot-integrity review

No correctness defect was found and no reviewer code/test correction was necessary. Reviewed the complete restore/test diff, PRD/implementation artifacts, retained reproduction, live JSON receipts and both deployment-contract additions. The implementation remains a direct extension of the existing restore flow, without a new downloader or retry policy.

Selected asset state, non-bool integer size and strict SHA-256 metadata are validated before destination setup/download. Structural metadata failures, duplicate selected names and malformed selected fields cannot authorize bootstrap. An explicitly missing selected name in a structurally valid asset list retains the existing first-run behavior. Streaming enforces the expected size and unchanged 100 MiB ceiling; final length/hash agreement precedes every SQLite/catalog read. Failure cleanup and initial destination refusal remain intact. Successful placement preserves the complete verified bytes, including historical observations and original times.

The regression suite meaningfully distinguishes valid-but-stale SQLite from the pinned asset, including an equal-length changed database, in both bootstrap modes. It verifies exact streamed success and prior/current history, early metadata rejection, short/excess/wrong-digest cleanup before SQLite, matching-digest non-SQLite failure, wrong catalog and overwrite refusal. Fixed URL construction, metadata-only Authorization, metadata redirect refusal and credential-free asset/CDN requests are preserved.

Pinning establishes agreement with the metadata read for that invocation. It does not provide global publication atomicity or guarantee that an asset cannot be replaced after that read. Both contract additions and task artifacts state that limitation; no runtime/source freshness, schema migration or data-publication claim is introduced.

Verification:

- Focused restore suite: **79 passed**, supplied by the implementer on the identical reviewed script.
- Root's unchanged full safe suites: **1,202 shared / 1,109 clean-tree tests passed**, eight existing warnings. The shared tree includes 93 inactive Circle cases. These full results were reused as requested.
- Independently ran exact CI Ruff plus the restore test file, shared JavaScript syntax, changed Python compilation and whitespace checks: **passed**. No type checker is configured.
- Script SHA256 remains `04cd373b76eb6a807708adf65adcba943cfa1821f560c170f756b209c0ceadb8`.

The retained stale-file reproduction now fails without a destination in both bootstrap modes. Root's separate read-only live receipt reports byte/digest agreement for cycling (21 sources / 58 observations) and tools (13 sources / 36 observations), with unchanged metadata before/after the observed restores and byte-preserving validation. This reviewer read only those public JSON receipts, not the downloaded databases.

No unresolved implementation blocker remains. Root owns publication and CI/merge. Only this review note was written; no network, credential access, operational/public database read, source refresh, commit, push or deployment occurred during review. Circle and root-owned edits were preserved.
