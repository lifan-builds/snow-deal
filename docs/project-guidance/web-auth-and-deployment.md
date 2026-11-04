# Web, auth, and deployment contracts

The web UI is server-rendered Jinja2 plus htmx and vanilla JavaScript; do not introduce a SPA/build framework. Shared card markup remains in `_card.html`. Avoid nested anchors. Use keyword-style `TemplateResponse(request=..., name=..., context=...)`.

Filter routes share `_fetch_deals()`. htmx pagination replaces the closest `.load-more-wrap` with `outerHTML`. Active length filters exclude rows with null lengths. Analytics calls are fire-and-forget and must not carry credentials or medical/financial data.

Invite gating is controlled by `PUBLIC_MODE`; JWT cookies require `SECRET_KEY`. `ADMIN_KEY` is an admin bypass and must never appear in source, logs, tests, or artifacts. Turso-backed auth operations must preserve local development fallback and synchronization semantics.

Vercel functions treat deal data as read-only. The build downloads or uses an existing SQLite snapshot, copies static assets, and bundles the database; fresh scrape data requires a deployment. Do not invoke Vercel, Render hooks, GitHub release upload, schema migration, or cloud synchronization during routine validation.

Catalog history restoration authenticates only its fixed GitHub release-metadata request with the workflow's existing read-only `GITHUB_TOKEN`; do not set client-wide authorization headers or send the token to public asset/CDN downloads. Metadata redirects and HTTP errors fail closed even with bootstrap requested. A rate-limit failure cannot authorize discarding history.

The snow build may compact its newly downloaded temporary SQLite snapshot after migrations and review reconciliation. Validate integrity, listing count and freshness before and after `VACUUM`, then atomically replace the build destination. Compaction must preserve all current and historical rows and schema; it is not retention cleanup. The explicit skip-download path must remain byte-preserving, and operational/auth databases are outside this build step.
