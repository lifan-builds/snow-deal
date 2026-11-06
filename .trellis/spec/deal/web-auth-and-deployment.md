# Web, auth, and deployment contracts

The web UI is server-rendered Jinja2 plus htmx and vanilla JavaScript; do not introduce a SPA/build framework. Shared card markup remains in `_card.html`. Avoid nested anchors. Use keyword-style `TemplateResponse(request=..., name=..., context=...)`.

Filter routes share `_fetch_deals()`. htmx pagination replaces the closest `.load-more-wrap` with `outerHTML`. Active length filters exclude rows with null lengths. Analytics calls are fire-and-forget and must not carry credentials or medical/financial data.

Invite gating is controlled by `PUBLIC_MODE`; JWT cookies require `SECRET_KEY`. `ADMIN_KEY` is an admin bypass and must never appear in source, logs, tests, or Trellis artifacts. Turso-backed auth operations must preserve local development fallback and synchronization semantics.

Vercel functions treat deal data as read-only. The build downloads or uses an existing SQLite snapshot, copies static assets, and bundles the database; fresh scrape data requires a deployment. Do not invoke Vercel, Render hooks, GitHub release upload, schema migration, or cloud synchronization during routine validation.

## Compressed snow snapshot packaging

See docs/project-guidance/web-auth-and-deployment.md for exact-byte gzip packaging, pre-import path initialization, atomic verified temporary reconstruction, explicit-path/local compatibility and history-preserving release checks. The source snapshot is unchanged; runtime has no network download or migration authority.

## Shared catalog size facets

See docs/project-guidance/web-auth-and-deployment.md for the existing-size-key facet grouping contract, stable original-label representatives, legacy/unknown request selection, raw offer/history preservation and required query/HTTP regression cases. This is presentation normalization, not expanded fit matching.

## Catalog release asset integrity

`scripts/restore_catalog.py` requires unique selected asset metadata: uploaded state, positive integer size (excluding bool) within the existing 100 MiB budget, and strict `sha256:` plus 64 hexadecimal characters. Reject missing/malformed metadata before destination setup or download, including bootstrap requests. Only an explicitly absent asset in well-formed metadata can authorize first-run bootstrap.

See docs/project-guidance/web-auth-and-deployment.md for incremental streaming length/hash verification before SQLite, exact successful snapshot/history bytes, temporary cleanup and atomic placement. Preserve fixed download URLs, metadata-only authentication, overwrite refusal and SQLite/catalog checks. Integrity failures cannot become bootstrap or trigger automatic retries; valid stale/same-sized changed SQLite must fail against the pinned metadata.

## Merchant pricing caveats

See docs/project-guidance/web-auth-and-deployment.md under Merchant pricing caveats. Show the selected offer's optional escaped price note beside its listed price/details and each observation's own note in its dated price cell. Legacy absence stays blank and means only unrecorded; never backfill today's or another variant's note. Reuse existing styles and preserve stock, calculations, fit, ranking/counts, schema and daily history retention.
