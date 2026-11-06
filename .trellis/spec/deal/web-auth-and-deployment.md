# Web, auth, and deployment contracts

The web UI is server-rendered Jinja2 plus htmx and vanilla JavaScript; do not introduce a SPA/build framework. Shared card markup remains in `_card.html`. Avoid nested anchors. Use keyword-style `TemplateResponse(request=..., name=..., context=...)`.

Filter routes share `_fetch_deals()`. htmx pagination replaces the closest `.load-more-wrap` with `outerHTML`. Active length filters exclude rows with null lengths. Analytics calls are fire-and-forget and must not carry credentials or medical/financial data.

Invite gating is controlled by `PUBLIC_MODE`; JWT cookies require `SECRET_KEY`. `ADMIN_KEY` is an admin bypass and must never appear in source, logs, tests, or Trellis artifacts. Turso-backed auth operations must preserve local development fallback and synchronization semantics.

Vercel functions treat deal data as read-only. The build downloads or uses an existing SQLite snapshot, copies static assets, and bundles the database; fresh scrape data requires a deployment. Do not invoke Vercel, Render hooks, GitHub release upload, schema migration, or cloud synchronization during routine validation.

The snow refresh workflow may skip Chromium installation only when an explicit comma-separated retailer selection consists entirely of configured stores with `use_browser=False`. Read that flag from the store registry; retain browser setup for full/scheduled refreshes, browser or mixed selections, and unknown or malformed input. Pass the workflow input through an environment variable, preserve exact retailer names and the existing scraper CLI validation, and consume the helper's boolean step output. This changes dependency setup only, not source completeness, publication or history checks.

## Compressed snow snapshot packaging

See docs/project-guidance/web-auth-and-deployment.md for exact-byte gzip packaging, pre-import path initialization, atomic verified temporary reconstruction, explicit-path/local compatibility and history-preserving release checks. The source snapshot is unchanged; runtime has no network download or migration authority.

## Shared catalog size facets

See docs/project-guidance/web-auth-and-deployment.md for the existing-size-key facet grouping contract, stable original-label representatives, legacy/unknown request selection, raw offer/history preservation and required query/HTTP regression cases. This is presentation normalization, not expanded fit matching.

## Catalog release asset integrity

`scripts/restore_catalog.py` requires unique selected asset metadata: uploaded state, positive integer size (excluding bool) within the existing 100 MiB budget, and strict `sha256:` plus 64 hexadecimal characters. Reject missing/malformed metadata before destination setup or download, including bootstrap requests. Only an explicitly absent asset in well-formed metadata can authorize first-run bootstrap.

See docs/project-guidance/web-auth-and-deployment.md for incremental streaming length/hash verification before SQLite, exact successful snapshot/history bytes, temporary cleanup and atomic placement. Preserve fixed download URLs, metadata-only authentication, overwrite refusal and SQLite/catalog checks. Integrity failures cannot become bootstrap or trigger automatic retries; valid stale/same-sized changed SQLite must fail against the pinned metadata.

## Merchant pricing caveats

See docs/project-guidance/web-auth-and-deployment.md under Merchant pricing caveats. Show the selected offer's optional escaped price note beside its listed price/details and each observation's own note in its dated price cell. Legacy absence stays blank and means only unrecorded; never backfill today's or another variant's note. Reuse existing styles and preserve stock, calculations, fit, ranking/counts, schema and daily history retention.

## Snow retailer filter counts

`query_deals(count_by_store=True)` returns grouped counts of the same effective selected offers and eligibility as the visible query, before pagination. Ignore only the selected retailer; preserve all other filters, including clothing, exact size/stock, currency, reference/price limits, freshness, exclusions, year/length and reviews. Reuse one SQL selection/filter path and one grouped query, rather than querying each store or materializing all cards. Configured stores without matches render zero. Operational `store_status` continues reporting ingested source rows.

The initial page and normal htmx filter responses share escaped retailer option markup. The latter replaces the complete `#store-filter` select through an out-of-band outerHTML swap, retaining its id, name, requested selection and an unknown selected value. Do not insert options through an innerHTML OOB swap: the browser can select a different retailer while preserving the old selected attribute, causing the next request to change stores. Confirm the live selected value and next submitted query in a native browser, not only rendered attributes. Load-more responses must not replace retailer options or perform the grouped facet query. Category/brand facet behavior stays separate. Regression checks cover selected-variant thresholds, unknown stock, excluded/stale/future rows, clothing, every other query filter, unchanged health counts, one grouped query and initial/fragment/load-more rendering.
