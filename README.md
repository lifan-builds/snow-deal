# Deal Aggregator

Find exceptional discounts on expensive products across specialist retailers. Browse the deepest percentage discounts first, with the original price, sale price, and dollar savings visible together.

Fresh Powder is the first catalog: ski and snowboard gear. The reusable ingestion code lives in `common/`; each catalog owns its product rules, retailer selection, identity, and customer experience.

## Layout

```text
common/
  deal_common/                # Product model, retailer settings, parsers, HTTP pagination, rate limiting
  tests/                      # Offline tests for shared components
catalogs/
  fresh-powder/
    src/aggregator/           # Snow catalog, scraper orchestration, SQLite queries, reviews, web app
    src/snow_deals/           # Existing CLI and BlueZone parser
    tests/                   # Fresh Powder regression tests
    deploy/                  # Docker and Render startup
    tampermonkey/            # Snow-specific userscript
    docs/images/             # Product screenshots
    history/                 # Preserved architecture/planning records
    PLAN.md                  # Preserved product growth plan
  cycling/                   # Proposed second catalog; research only
scripts/                      # Workspace checks and default Vercel build adapter
app.py, api/, vercel.json      # Existing Fresh Powder deployment entrypoints
PLANS.md                      # Workspace refactor decisions and verification
```

Read [the methodology](docs/METHODOLOGY.md), [common component boundaries](common/README.md), and [the cycling proposal](catalogs/cycling/README.md).

## Development

Python 3.11+ is required. From the workspace root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python scripts/check.py -q
PUBLIC_MODE=1 .venv/bin/uvicorn aggregator.web.app:create_app --factory --reload
```

The check runner clears inherited service credentials and uses temporary databases. It does not load `.env`, fetch retailer data, or use existing local databases. Browser binaries are only needed for an intentional live scrape, not these tests.

For a safe UI preview with synthetic offers and temporary databases, run `.venv/bin/python scripts/preview_offers.py` and open `http://127.0.0.1:8765`. This demonstrates size-specific prices, percent-first ranking, original-price filtering, and browser-local saved searches. The sample deals are not retailer inventory.

A single root installation provides `deal_common`, the existing `aggregator` and `snow_deals` import names, and both existing CLI commands. No second install inside the catalog is needed. Templates and static assets are included in the package.

The web command starts the Fresh Powder app with public local access and a new, initially empty database. For invite-gated development configure your own `SECRET_KEY`. See [Fresh Powder](catalogs/fresh-powder/README.md) for deployment and data paths.

## Migration notes

The repository is now the Deal Aggregator workspace. This active checkout retains the physical path `/Users/lfan/Project/fresh-powder`; no parent directory, Git remote, cloud project, or existing worktree was renamed.

Old ignored databases, credentials, deployment state, browser state, and installed dependencies were left in place. Legacy directories may therefore remain locally even though tracked source moved. Reinstall with the root command above. To use an existing local database, explicitly set `DATABASE_PATH` and `AUTH_DB_PATH` to its existing absolute path; migration does not discover or copy it automatically.

Existing research in `docs/research/` and task media in `media/` retain their paths for current chats. Historical Fresh Powder plans are preserved in the catalog. Nothing in this refactor publishes or deploys changes.

The November 2 implementation also integrates the newer production application and retains Shopify variant offers and dated observations. Old snapshots need schema migration and a fresh scrape to populate variants. Schema migration alone does not establish size availability. HTML-only sources retain explicitly unknown stock unless their parser supplies variant evidence. See the [implementation receipt](docs/research/2026-11-02-deal-site-landscape/execution/IMPLEMENTATION.md) for verification and rollout limits.
