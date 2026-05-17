# FreshPowder — Aggregator

Multi-store deal aggregator for ski and snowboard gear. Scrapes 24 retailers, integrates 1,200+ review scores from OutdoorGearLab (skis, boots, gear) and The Good Ride (snowboards, bindings, boots, jackets), stores deal snapshots in SQLite, and serves a ranked dashboard via FastAPI + htmx. Two-pass fuzzy matching links reviews to deals with model family fallback. Includes admin panel for invite code management and analytics dashboard for tracking user behavior. Deployed on Vercel with GitHub Actions cron for automated scraping; Render/Docker support is retained as a fallback. Part of the [snow-deals](../) monorepo.

**Live site:** [snow-deals.onrender.com](https://snow-deals.onrender.com)

## Getting Started

### Prerequisites

- Python 3.11+
- The parent `snow_deals` package installed (see repo root)
- Playwright Chromium browser (`playwright install chromium`)

### Installation

```bash
# From the repo root, install the parent package
pip install -e .

# Then install the aggregator
cd aggregator
pip install -e .

# Install Playwright browser
playwright install chromium
```

### Usage

#### Scrape all stores

```bash
snow-deals-agg refresh
```

#### Fetch review scores

```bash
# Fetch from both sources (OutdoorGearLab + The Good Ride)
snow-deals-agg fetch-reviews

# Fetch from a specific source
snow-deals-agg fetch-reviews --source tgr   # The Good Ride (1,800+ reviews: snowboards, bindings, boots, jackets)
snow-deals-agg fetch-reviews --source ogl   # OutdoorGearLab (ski/boot/gear reviews, 26 categories)
```

#### Query deals from the CLI

```bash
# Top deals across all stores
snow-deals-agg deals

# Filter by category and minimum discount
snow-deals-agg deals --category skis --min-discount 20

# Filter by store
snow-deals-agg deals --store "Evo" --limit 25
```

#### Manage invite codes

```bash
# Generate 10 invite codes
snow-deals-agg generate-codes 10

# List all codes and their status (available/used)
snow-deals-agg list-codes
```

#### Web UI

```bash
# Run locally with admin bypass in public mode
PUBLIC_MODE=1 ADMIN_KEY=mysecret uvicorn aggregator.web.app:create_app --factory --reload
# Open http://localhost:8000/?admin_key=mysecret
```

The web UI provides:
- Live filtering by category, store, brand, discount percentage, and ski/snowboard length range via htmx
- Review score badges (color-coded) with award text and "Read review" links on matched deal cards
- "Top reviewed" sort and "Reviewed only" filter to surface expert-validated gear
- Search bar with debounced queries
- Sort by discount, price, store, top reviewed, or newest
- Tax-free filter (Canadian stores + no-nexus stores)
- CAD price display for Canadian stores (`C$` prefix + `CAD` tag)
- Sticky toolbar with search and filters
- Compact/comfortable view toggle
- "New since last visit" badges
- Load-more pagination (60 deals per page)
- Filter state persisted in URL (survives back-navigation)
- Store status dashboard at `/status` with data freshness indicators
- Optional invite-only access via `PUBLIC_MODE` (reusable codes support max 5 uses each)
- Admin panel at `/admin/codes` for generating and viewing invite codes
- Analytics dashboard at `/admin/stats` — click tracking, popular filters, top deals

## Deployment

The primary website is deployed on **Vercel** with scraping running on **GitHub Actions**:

- **Scraping:** GitHub Actions cron runs on schedule, uses Playwright for JS-rendered stores, uploads `deals.db` as a GitHub Release
- **Serving:** Vercel installs the root Python project dependencies, runs `python scripts/vercel_build.py`, bundles the downloaded `aggregator/deals.db`, and serves FastAPI through the root `app.py` entrypoint
- **Static assets:** The Vercel build copies `aggregator/aggregator/web/static` to `public/static` for direct static serving; FastAPI still mounts the package static directory for local and fallback serving
- **Deal data:** The bundled SQLite deal database is read-only in Vercel functions. Fresh deal data requires a new Vercel deployment after the scrape workflow publishes a new `latest-data` release
- **Auth:** Invite codes stored in Turso cloud SQLite (persist across redeploys). Sessions use JWT signed cookies (stateless, no DB lookup). Admin access via `ADMIN_KEY` env var
- **Admin:** `/admin/codes` for code management, `/admin/stats` for analytics dashboard

### Vercel Setup

1. Import the repository into Vercel.
2. Leave the project root at the repository root.
3. Use the committed `vercel.json`; no framework preset is required.
4. Configure the required environment variables in the Vercel dashboard.
5. Deploy. The build must be able to download the public `deals.db` release or use `DEALS_DB_DOWNLOAD_URL` to point at another SQLite snapshot.

### Vercel Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_PATH` | Optional override for the deals SQLite database path; normally omit it so the app uses `aggregator/deals.db` |
| `DEALS_DB_READ_ONLY` | Set for Vercel so startup validates the deal DB without schema writes |
| `AUTH_DB_PATH` | Local embedded Turso replica path; use `/tmp/auth_replica.db` on Vercel |
| `TURSO_DIRECT_CONNECTION` | Use direct Turso connections instead of embedded replica sync; set to `1` on Vercel |
| `DEALS_DB_DOWNLOAD_URL` | Optional build-time URL for the latest `deals.db` snapshot |
| `VERCEL_SKIP_DB_DOWNLOAD` | Optional local escape hatch; requires an existing valid `aggregator/deals.db` |
| `PUBLIC_MODE` | Set to disable invite gating and make the deal pages public |
| `ADMIN_KEY` | Admin access key |
| `TURSO_URL` | Turso database URL for auth, events, waitlist, and invite code persistence |
| `TURSO_AUTH_TOKEN` | Turso auth token |
| `SECRET_KEY` | JWT signing key for session cookies; required whenever `PUBLIC_MODE` is not enabled |

### Updating Deal Data On Vercel

Vercel functions cannot rely on persistent writable disk. The scrape workflow should publish `deals.db`, then trigger a Vercel deployment so the next build bundles the new database. A Vercel deploy hook is the simplest production workflow:

1. In Vercel, create a deploy hook for the production branch.
2. Store it as a GitHub Actions secret such as `VERCEL_DEPLOY_HOOK_URL`.
3. After the scrape workflow publishes the `latest-data` release, call the hook.

Render remains available as a fallback deployment target.

### Render Auto-Redeploy

The scrape workflow already supports redeploying Render after each successful data refresh.

1. In Render, open the web service and create a **Deploy Hook**.
2. Copy the hook URL into the GitHub Actions secret `RENDER_DEPLOY_HOOK_URL`.
3. Keep `DATABASE_PATH` pointed at the mounted path used by the container (`/app/data/deals.db` by default).

When that secret is present, `.github/workflows/scrape.yml` triggers Render after publishing the `latest-data` release asset.

### Environment Variables (Render)

| Variable | Purpose |
|----------|---------|
| `DATABASE_PATH` | Path to deals SQLite database (default: `./deals.db`) |
| `MAX_DB_STALENESS_HOURS` | Startup warning threshold for the downloaded `deals.db` freshness (default: `18`) |
| `PUBLIC_MODE` | Set to `1` to disable invite gating and make the site public |
| `ADMIN_KEY` | Admin access key (visit `/?admin_key=VALUE` to authenticate) |
| `TURSO_URL` | Turso database URL for auth persistence (e.g. `libsql://mydb.turso.io`) |
| `TURSO_AUTH_TOKEN` | Turso auth token (from Turso dashboard) |
| `SECRET_KEY` | JWT signing key for session cookies; required whenever `PUBLIC_MODE` is not enabled |
| `GITHUB_TOKEN` | (Optional) For downloading `deals.db` from private repos |

## Development

```bash
pip install -e ".[dev]"

# Run tests (71 tests across 8 test files)
pytest tests/ -v

# Lint
ruff check .
```

### Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_parse_price.py` | 8 | Shared price parser (USD, CAD, commas, edge cases) |
| `test_categorizer.py` | 15 | Keyword categorization (compound terms, URL fallback, exclusion, brand fallback, boot disambiguation) |
| `test_reviews.py` | 10 | Brand extraction, normalization, fuzzy matching |
| `test_parsers.py` | 9 | AlpineShopVT, ColoradoDiscount, SacredRide HTML parsing |
| `test_db.py` | 8 | SQLite CRUD, filters, upsert, brand query, store status |
| `test_browser_config.py` | 5 | Store config registry, aliases, raw product parsing |
| `test_scraper.py` | 2 | Kids filter, product-to-deal conversion, brand categorization |
| `test_web_routes.py` | 5 | Public mode, auth redirects, robots.txt, rate limiting |

## Project Structure

```
aggregator/
├── aggregator/
│   ├── config.py          # Store registry (24 stores), category keywords, exclude keywords, brand/model name sets
│   ├── models.py          # AggregatedDeal dataclass (sizes, length_min, length_max)
│   ├── categorizer.py     # Keyword + brand-based categorization with boot disambiguation and exclusion filter
│   ├── db.py              # SQLite schema (deals, reviews), CRUD, store status, migrations
│   ├── auth_db.py         # Turso cloud SQLite for auth (invite codes, sessions, events)
│   ├── auth.py            # JWT session auth middleware + admin bypass (stateless session validation)
│   ├── scraper.py         # Multi-store async scraper with dynamic parser registry
│   ├── reviews.py         # OGL + TGR review scrapers (7 sitemaps), two-pass fuzzy matcher with family fallback
│   ├── browser.py         # Playwright headless browser with per-store JS extractors
│   ├── cli.py             # Click CLI (refresh, deals, fetch-reviews, generate-codes, list-codes)
│   ├── parsers/
│   │   ├── common.py      # Shared parse_price() used by all BS4 parsers
│   │   ├── alpineshopvt.py, thecircle.py, coloradodiscount.py, sacredride.py
│   └── web/               # FastAPI app with htmx templates, admin panel, analytics dashboard
├── tests/                 # 71 tests (parsers, DB, categorizer, reviews, browser, scraper, web)
├── pyproject.toml
└── README.md
```

## Supported Stores

| Store | Type | Tax Free | Status |
|-------|------|-----------|--------|
| Aspen Ski and Board | Shopify | Yes | Active |
| PRFO | Shopify | Yes (CA) | Active |
| Sports Basement | Shopify | No | Active |
| Colorado Ski Shop | Shopify | No | Active |
| Ski Depot | Shopify | No | Active |
| BlueZone Sports | BS4 | No | Active |
| Colorado Discount Skis | httpx | No | Active |
| Alpine Shop VT | Playwright (BigCommerce) | No | Active |
| The Circle Whistler | Playwright (Lightspeed) | Yes (CA) | Active |
| Evo | Playwright | No | Active |
| Backcountry | Playwright (Chakra UI) | No | Active |
| Steep & Cheap | Playwright (Chakra UI) | No | Active |
| The House | Playwright (GTM) | No | Active |
| Corbetts | Playwright (BigCommerce) | Yes (CA) | Active |
| Level Nine Sports | Playwright (Chakra UI) | No | Active |
| Peter Glenn | Playwright (BigCommerce) | No | Active |
| Sacred Ride | BS4 (Avada/WooCommerce) | Yes (CA) | Active |
| Comor Sports | Shopify | Yes (CA) | Active |
| Ski Pro AZ | Shopify | Yes | Active |
| First Stop Board Barn | Shopify | Yes | Active |
| Fresh Skis | Shopify | Yes (CA) | Active |
| Rude Boys | Shopify | Yes (CA) | Active |
| Skiis & Biikes | Shopify | Yes (CA) | Active |
| Skirack | Shopify | Yes | Active |

## License

MIT
