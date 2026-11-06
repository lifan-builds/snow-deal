# Implementation

1. Validate selected metadata before destination setup/download: uploaded state, integer size (not bool) >0 and <=MAX_BYTES, exact sha256 digest with 64 hexadecimal characters. Reject missing or unsupported metadata. Validate metadata structure defensively without changing missing-asset bootstrap semantics.
2. Incrementally hash while streaming; enforce both metadata expected length and existing byte budget, then compare exact final length and digest before opening SQLite. Keep temporary cleanup and atomic destination placement.
3. Add behavior tests using valid temporary snapshots for stale content (including equal-length mismatch), exact byte/history success, metadata errors, short/excess download, bootstrap refusal on all integrity failures, token redirect scope and preserved existing destination.
4. Implement agent runs focused tests/lint. Independent check agent reviews entire diff and full suite. Root verifies public restored copies against metadata read-only, records evidence, publishes PR, waits CI/preview and merges. Existing runtime data and deployments remain untouched.
