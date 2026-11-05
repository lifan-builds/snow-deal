# Web, auth, and deployment contracts

The web UI is server-rendered Jinja2 plus htmx and vanilla JavaScript; do not introduce a SPA/build framework. Shared card markup remains in `_card.html`. Avoid nested anchors. Use keyword-style `TemplateResponse(request=..., name=..., context=...)`.

Filter routes share `_fetch_deals()`. htmx pagination replaces the closest `.load-more-wrap` with `outerHTML`. Active length filters exclude rows with null lengths. Analytics calls are fire-and-forget and must not carry credentials or medical/financial data.

Invite gating is controlled by `PUBLIC_MODE`; JWT cookies require `SECRET_KEY`. `ADMIN_KEY` is an admin bypass and must never appear in source, logs, tests, or Trellis artifacts. Turso-backed auth operations must preserve local development fallback and synchronization semantics.

Vercel functions treat deal data as read-only. The build downloads or uses an existing SQLite snapshot, copies static assets, and bundles the database; fresh scrape data requires a deployment. Do not invoke Vercel, Render hooks, GitHub release upload, schema migration, or cloud synchronization during routine validation.

## Compressed snow snapshot packaging

See docs/project-guidance/web-auth-and-deployment.md for exact-byte gzip packaging, pre-import path initialization, atomic verified temporary reconstruction, explicit-path/local compatibility and history-preserving release checks. The source snapshot is unchanged; runtime has no network download or migration authority.
