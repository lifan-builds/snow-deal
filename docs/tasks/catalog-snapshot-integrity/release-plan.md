# Snapshot integrity release

Publish the reviewed restoration script, regression tests, mirrored contract and evidence under standing approval. Require full isolated offline checks, CI and preview to pass before merging. The existing catalog-refresh workflow already invokes this script before source refresh: merged main makes the guard available to subsequent runs. No workflow permission, live catalog data, source timestamp or serving runtime changes are needed, and this release does not require a manual refresh, public asset upload or deployment.

Verification: replay the exact previously accepted public stale file (both bootstrap modes must reject it without destination), pass synthetic same-size/different-content tests, and restore both public assets to new explicit local paths. Compare file size and SHA-256 against public release metadata before and after, verify SQLite/catalog identity and history presence read-only, and prove those checks preserve the downloaded bytes. Retain the failed old behavior as evidence.

Operational effect: missing/unsupported digest, malformed size/state, ambiguous asset metadata or byte mismatch now fails the refresh before publication. Do not respond by enabling bootstrap or replacing the source database with an empty one. A later invocation may retry after the asset settles. Matching a metadata digest does not prove no newer release can exist afterward.

Recovery: investigate an integrity failure using the retained public metadata and actual bytes. Revert only the code change through a reviewed PR if needed; do not rewrite observations or republish data to hide a failed download. The existing baseline commit is d337115143af42cbd9df8d65873601903870b76f.
