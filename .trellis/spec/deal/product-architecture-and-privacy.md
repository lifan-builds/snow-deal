# Product architecture and privacy

## Boundaries

- `aggregator/` is the primary FastAPI/Jinja2/htmx application and scraper orchestration package.
- `snow_deals/` is the secondary Python CLI and owns reusable Shopify/BlueZone parsers and `Product`.
- `tampermonkey/` is a secondary browser userscript.
- Deal snapshots use SQLite; auth, invite, session, event, and waitlist persistence uses Turso when configured and local SQLite only for development.
- Scheduled scraping runs separately from web serving. Vercel serves a bundled read-only deal database; Render remains a fallback.

## Privacy contract

Never commit or expose `.env`, cookies, Turso tokens, JWT/admin secrets, browser state, auth databases, scraped database files, deploy hooks, or private operational tokens. Existing database and sidecar files are outside migration scope. Do not open or mutate them for generic validation.

Environment keys are configuration, never values: `DATABASE_PATH`, `DEALS_DB_READ_ONLY`, `AUTH_DB_PATH`, `TURSO_DIRECT_CONNECTION`, `DISABLE_APP_LIFESPAN`, `DEALS_DB_DOWNLOAD_URL`, `VERCEL_SKIP_DB_DOWNLOAD`, `PUBLIC_MODE`, `ADMIN_KEY`, `TURSO_URL`, `TURSO_AUTH_TOKEN`, and `SECRET_KEY`.

The public/private historical notes conflict. Treat the current README's public-repository rule as controlling: source may be public, but credentials and operational/local data must never be published.
