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
  cycling/                   # Big Ring: cycling rules, sources, branding, and CLI
  tools/                     # Bench Drop: workshop/power-tool rules, sources, branding, and CLI
scripts/                      # Workspace checks and default Vercel build adapter
app.py, api/, vercel.json      # Existing Fresh Powder deployment entrypoints
PLANS.md                      # Workspace refactor decisions and verification
```

Read [the methodology](docs/METHODOLOGY.md), [common component boundaries](common/README.md), [Big Ring](catalogs/cycling/README.md), and [Bench Drop](catalogs/tools/README.md).

The cycling and tools sites share `common/deal_common/catalog/`: atomic source snapshots, dated observations, matching-variant filters, percentage-first ranking, pagination, responsive templates, and browser-local saved searches. Each catalog owns its classifications and visual assets. Their [delivery record](docs/tasks/cycling-tools-sites/DELIVERY.md) includes local previews, source limits, and independent deployment packaging.

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

A single root installation provides `deal_common`, `aggregator`, `snow_deals`, `cycling_deals`, and `tool_deals`. The new commands are `cycling-deals` and `tool-deals`, each with `refresh --database PATH` and `serve --database PATH` subcommands. No second install inside the catalog is needed. Templates and static assets are included in the package.

The web command starts the Fresh Powder app with public local access and a new, initially empty database. For invite-gated development configure your own `SECRET_KEY`. See [Fresh Powder](catalogs/fresh-powder/README.md) for deployment and data paths.

## Migration notes

The repository is now the Deal Aggregator workspace. This active checkout retains the physical path `/Users/lfan/Project/fresh-powder`; no parent directory, Git remote, cloud project, or existing worktree was renamed.

Old ignored databases, credentials, deployment state, browser state, and installed dependencies were left in place. Legacy directories may therefore remain locally even though tracked source moved. Reinstall with the root command above. To use an existing local database, explicitly set `DATABASE_PATH` and `AUTH_DB_PATH` to its existing absolute path; migration does not discover or copy it automatically.

Existing research in `docs/research/` and task media in `media/` retain their paths for current chats. Historical Fresh Powder plans are preserved in the catalog. Nothing in this refactor publishes or deploys changes.

The November 2 implementation also integrates the newer production application and retains Shopify variant offers and dated observations. Old snapshots need schema migration and a fresh scrape to populate variants. Schema migration alone does not establish size availability. HTML-only sources retain explicitly unknown stock unless their parser supplies variant evidence. See the [implementation receipt](docs/research/2026-11-02-deal-site-landscape/execution/IMPLEMENTATION.md) for verification and rollout limits.

## Competitive quality benchmark

See [the ten-metric comparison](docs/COMPETITIVE-BENCHMARK.md), [latest measured matrix](docs/benchmarks/2026-11-05-incycle-matrix.md), and [verified Incycle rollout](docs/benchmarks/2026-11-05-incycle-rollout.json). Big Ring has 21 fresh configured sources, 1,477 qualifying in-stock listings and 203 listings at least 40% off in that November 5 snapshot. Run `python scripts/benchmark.py docs/benchmarks/2026-11-05-incycle-matrix.json --require-lead` to test a market-lead claim. The matrix records four strict leads across 260 comparisons; missing or incomparable evidence and parity do not establish an all-metrics lead.

### Earlier expansion checkpoints

The records below retain their original counts and release status; use the verified rollout above for the latest production checkpoint.

The [source follow-up](docs/tasks/source-expansion/SATURATION.md) extends Fresh Powder’s admission process to 16 cycling and nine tools retailers. It includes isolated probes, full pagination, USD/stock/identity checks, shipping/condition exclusions and separate merchant samples. The [prior competitive pass](docs/benchmarks/2026-11-03-competitive-continuation.md) has 1,142 qualifying cycling listings (87 at least 40% off) and 351 tools listings (21 at least 40% off), with stronger frame-size and condition checks. Common ingestion also supports Grizzly’s exact-SKU public structured data. This is measured public-feed coverage, not exhaustive market coverage or publication.

The separate [Taylor adapter follow-up](docs/tasks/taylor-source/IMPLEMENTATION.md) brings tools to ten retailers, 352 qualifying listings and 22 deep deals. It adds bounded product-detail discovery to common ingestion while keeping source-specific SKU/option rules in the parser. At that checkpoint, release `7798318` was the nine-source publication candidate and the follow-up was local work beyond its approval scope.

The [Fasteners follow-up](docs/tasks/fasteners-source/IMPLEMENTATION.md) further expands tools to 11 retailers, 409 qualifying listings and 26 deep deals from six retailers. It reuses the existing Shopify pipeline after verifying the merchant’s current storefront redirects and prices. All 445 offline tests and both 30-offer merchant samples passed. At that checkpoint, this follow-up was local and outside release `7798318`.
