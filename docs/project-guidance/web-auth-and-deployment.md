# Web, auth, and deployment contracts

The web UI is server-rendered Jinja2 plus htmx and vanilla JavaScript; do not introduce a SPA/build framework. Shared card markup remains in `_card.html`. Avoid nested anchors. Use keyword-style `TemplateResponse(request=..., name=..., context=...)`.

Filter routes share `_fetch_deals()`. htmx pagination replaces the closest `.load-more-wrap` with `outerHTML`. Active length filters exclude rows with null lengths. Analytics calls are fire-and-forget and must not carry credentials or medical/financial data.

Invite gating is controlled by `PUBLIC_MODE`; JWT cookies require `SECRET_KEY`. `ADMIN_KEY` is an admin bypass and must never appear in source, logs, tests, or artifacts. Turso-backed auth operations must preserve local development fallback and synchronization semantics.

Vercel functions treat deal data as read-only. The build downloads or uses an existing SQLite snapshot, copies static assets, and bundles the database; fresh scrape data requires a deployment. Do not invoke Vercel, Render hooks, GitHub release upload, schema migration, or cloud synchronization during routine validation.

The snow refresh workflow may skip Chromium installation only when an explicit comma-separated retailer selection consists entirely of configured stores with `use_browser=False`. Read that flag from the store registry; retain browser setup for full/scheduled refreshes, browser or mixed selections, and unknown or malformed input. Pass the workflow input through an environment variable, preserve exact retailer names and the existing scraper CLI validation, and consume the helper's boolean step output. This changes dependency setup only, not source completeness, publication or history checks.

Catalog history restoration authenticates only its fixed GitHub release-metadata request with the workflow's existing read-only `GITHUB_TOKEN`; do not set client-wide authorization headers or send the token to public asset/CDN downloads. Metadata redirects and HTTP errors fail closed even with bootstrap requested. A rate-limit failure cannot authorize discarding history.

The snow build may compact its newly downloaded temporary SQLite snapshot after migrations and review reconciliation. Validate integrity, listing count and freshness before and after `VACUUM`, then atomically replace the build destination. Compaction must preserve all current and historical rows. The sole permitted schema change is dropping `idx_history_url` when PRAGMA metadata proves it is an ordinary nonunique, nonpartial index with exactly the same columns, order and collation as the retained primary-key index; unexpected definitions remain untouched. It is not retention cleanup. The explicit skip-download path must remain byte-preserving, and operational/auth databases are outside this build step.

The snow build packages the validated database as deterministic gzip plus an original-byte-count/SHA256 manifest. Include these artifacts explicitly and exclude the uncompressed build copy from the function. Preserve the source DB bytes. At application initialization, before importing consumers of DB_PATH, materialize only the packaged snapshot into a digest-named temporary file, verify bytes/hash, then atomically publish the local copy. Serialize extraction per digest and recheck the cache under the lock to limit temporary storage to one large copy; remove only that digest's abandoned extraction temporaries under the lock. Selecting compressed runtime data must force read-only DB access even outside Vercel. Concurrent initializers must not expose partial databases; corrupt streams/caches fail or rebuild without serving bad data. Explicit DATABASE_PATH wins, and local uncompressed development remains supported. This is local reconstruction, not permission for runtime downloads, migrations, history cleanup or auth-data access. Verify actual platform deployment headroom and exact current/historical rows after compression.

## Shared catalog size facets

### Scope / trigger

Cycling and tools size menus must not repeat labels which the existing `size_key` matcher already treats as equivalent. This is presentation only; it does not infer fit or expand size equivalence. Fresh Powder uses a separate web app.

### Signatures

`query(sources, filters, *, now=None)` retains `facets["size"]: list[str]`; `GET /?size=<label>` continues accepting original retailer labels and existing saved-search URLs.

### Contracts

Group only existing fresh, reported-in-stock facet labels by `size_key`. Select an existing label deterministically by length, case-folded spelling, then original spelling. After querying, resolve a known incoming alias to its representative for form selection, filter display and generated links. Preserve raw selected offer size/options/stock/price/reference/URL and all persisted observations.

### Validation and error behavior

Unknown requested labels remain selected, escaped and visible with the existing empty result. Unknown-stock, stale and future source labels cannot introduce facet entries. Compound labels and numeric-s sizes remain distinct unless `size_key` already equates them.

### Good / base / bad cases

M/MD/Medium collapse to one existing menu label and match the same offers. A unique model-size identifier stays unchanged. M/L must not become M; 50s must not become 50; a shorter menu must never discard matching offers.

### Required tests

Assert source-order-independent representatives, legacy and unknown selected form state, generated pagination links, escaped unknown values, preserved raw offers, ordering/counts/pagination, and fresh/stock facet membership. Replay explicit public snapshots read-only when assessing a release.

### Wrong versus correct

Wrong: rewrite stored merchant sizes to simplify the menu or deduplicate cards using display labels. Correct: deduplicate facet strings using existing matching semantics, while cards and history retain the exact merchant variant.

## Catalog release asset integrity

`scripts/restore_catalog.py` pins the selected release asset's metadata before downloading. Require a unique named asset with `state: uploaded`, an integer size (never bool) greater than zero and at most the existing 100 MiB `MAX_BYTES`, and a `sha256:` digest followed by exactly 64 hexadecimal characters. Missing, malformed or unsupported metadata fails before destination setup or the asset request, including with `--bootstrap`. Only an explicitly absent asset in well-formed metadata permits the existing first-run bootstrap.

Count bytes and update SHA-256 incrementally while streaming; stop on excess expected length or budget. Require exact final metadata length and digest before SQLite integrity/catalog/history checks. A valid old SQLite file, including a same-sized changed file, is not the pinned asset. Fail without placing a destination and clean temporary bytes on every mismatch; never silently bootstrap, retry or discard history. Successful restoration preserves the entire snapshot byte-for-byte before atomic placement. Retain fixed URL construction, metadata-only authentication and refusal to overwrite an existing destination. This verifies the metadata read for this invocation; it cannot promise that a publisher will never replace an asset afterward.

## Merchant pricing caveats

Shared catalog cards display a selected offer's nonempty `price_note` beside its listed price and inside Price & variant details, separate from stock status. The history table displays the note only in that dated observation's price cell, using the historical candidate value. Legacy offers/observations without the optional field stay readable and render no empty notice; explain that retailer pricing notes appear only when recorded, so a blank historical note does not establish that no caveat existed. Never backfill today's note or attach another selected variant's note.

Use normal escaped Jinja output for card/details/history notes and reuse existing styles. The optional JSON field requires no schema migration, stock warning, price calculation, filter/ranking change or separate Fresh Powder UI. Verify selected-variant rendering/escaping, historical absence, unchanged query population/ordering and the existing latest-successful-observation-per-UTC-day retention rule before source-scoped publication.

## Snow retailer filter counts

`query_deals(count_by_store=True)` returns grouped counts of the same effective selected offers and eligibility as the visible query, before pagination. Ignore only the selected retailer; preserve all other filters, including clothing, exact size/stock, currency, reference/price limits, freshness, exclusions, year/length and reviews. Reuse one SQL selection/filter path and one grouped query, rather than querying each store or materializing all cards. Configured stores without matches render zero. Operational `store_status` continues reporting ingested source rows.

The initial page and normal htmx filter responses share escaped retailer option markup. The latter replaces the complete `#store-filter` select through an out-of-band outerHTML swap, retaining its id, name, requested selection and an unknown selected value. Do not insert options through an innerHTML OOB swap: the browser can select a different retailer while preserving the old selected attribute, causing the next request to change stores. Confirm the live selected value and next submitted query in a native browser, not only rendered attributes. Load-more responses must not replace retailer options or perform the grouped facet query. Category/brand facet behavior stays separate. Regression checks cover selected-variant thresholds, unknown stock, excluded/stale/future rows, clothing, every other query filter, unchanged health counts, one grouped query and initial/fragment/load-more rendering.
