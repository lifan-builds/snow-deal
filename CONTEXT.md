# Context
<!-- context-harness:schema v3 -->

## Project
FreshPowder (snow-deal) is a ski & snowboard deal aggregator that tracks prices across 20+ North American retailers every 6 hours, matches expert review scores from OutdoorGearLab and GoodRide, and surfaces the best deals through a fast, filterable web interface. Features invite-gated access with a public marketing landing page, a secondary Tampermonkey userscript, and Python CLI.

## Structure
- `aggregator/` - Main product: FreshPowder web app (FastAPI, htmx, Turso/SQLite, Playwright)
- `tampermonkey/` - Browser userscript (secondary)
- `snow_deals/` - Python CLI (secondary)
- `.github/workflows/` - Cron scraper (every 6h)

## Operating Constraints

- Do not commit secrets (cookies.json, .env, Turso tokens) — they're in-tree and must stay untracked.
- Do not scrape without testing categorization first — mis-categorized products pollute the feed.
- Do not skip the freshness/stock checks when adding a new parser.
- Space-pad exclusion keywords (" used " not "used") to avoid substring false positives.
- Run python -m pytest aggregator/tests/ -x -q before commit.
- Verify selectors live via Playwright MCP before adding a new store.
- Web app boots cleanly (uvicorn aggregator.web.app:create_app --factory exits 0 startup).

## Workflow
- Setup: `cd aggregator && pip install -e .`
- Run: `uvicorn aggregator.web.app:create_app --factory --reload`
- Test: `python -m pytest aggregator/tests/ -x -q`
- Run Scrape: `python -m aggregator.cli scrape`

### Verification
- All tests pass (`python -m pytest aggregator/tests/ -x -q` exits 0)
- Scraper runs without parser errors (`python -m aggregator.cli scrape` exits 0)
## Learned Patterns
1. Exclusion keyword design: space-padded `" used "` prevents matching "unused"/"refused". Prepend space to search string so keywords match at start: `f" {name} {url}".lower()`.
2. Model name ambiguity: Single-word names like "frontier", "ultra", "hera" are too ambiguous. Must use brand-qualified multi-word entries.
3. Brand fallback categorization catches accessories as hardgoods — NOT_HARDGOODS_KEYWORDS must be aggressively expanded.
4. htmx load-more pattern: `hx-target="this"` on the button leaves the wrapper div. Must use `hx-target="closest .load-more-wrap"` with `hx-swap="outerHTML"`.
5. Headless Shopify (Hydrogen/Oxygen) stores return 404 on JSON API endpoints — must use Playwright browser scraping.
6. Shared `_JS_PARSE_PRICE` regex `[\d,]+\.\d{2}` fails on whole-dollar prices like "$1,150" — stores with non-decimal prices need custom `[\d,]+\.?\d*` regex.
7. SQLite Performance: Correlated subqueries (e.g., `scraped_at = (SELECT MAX(d2.scraped_at) FROM deals d2 WHERE d2.store = deals.store)`) degrade to O(N^2) as the table grows. Use an `INNER JOIN (SELECT store, MAX(scraped_at) FROM deals GROUP BY store)` to achieve O(N) performance.

## Language
<!-- Durable terms and agent discoveries. -->

## Relationships
- AGENTS.md is the small activation layer; CONTEXT.md is the durable source of truth.

## Flagged Ambiguities
- Project-specific verification commands may need confirmation.

## Imported Agent Notes
<!-- Migrated from the pre-v3 AGENTS.md during the one-time context-harness upgrade. Keep durable facts here; keep AGENTS.md small. -->

# Agent Guide

## Project Overview

**FreshPowder** (repo: `snow-deal`) is a ski & snowboard deal aggregator that tracks prices across 20+ North American retailers every 6 hours, matches expert review scores from OutdoorGearLab and GoodRide, and surfaces the best deals through a fast, filterable web interface. The app is invite-gated for controlled growth, with a public marketing landing page. A secondary Tampermonkey userscript and Python CLI exist for single-site browsing.

**Live at:** https://snow-deal.vercel.app

## Tech Stack

### Web Aggregator (primary — `aggregator/`)
- **Backend:** Python 3.12, FastAPI, aiosqlite
- **Frontend:** Jinja2 templates, htmx 2.0.4, vanilla JS, custom CSS (dark theme)
- **Database:** SQLite (deals), Turso cloud (auth/sessions/events)
- **Auth:** JWT-based invite codes, rate limiting
- **Deployment:** Vercel Python Functions for the primary site; Docker on Render retained as fallback
- **Scraping:** GitHub Actions cron (every 6h), httpx + BeautifulSoup4/lxml, Playwright (for JS-rendered/anti-bot sites)
- **Reviews:** OutdoorGearLab + GoodRide score matching

### Tampermonkey Userscript (secondary — `tampermonkey/`)
- Vanilla JS, Tampermonkey GM_ APIs

### Python CLI (secondary — `snow_deals/`)
- Python 3.11+, httpx, click, rich

## Project Structure

```
snow-deal/
├── aggregator/                    # Main product — FreshPowder web app
│   ├── aggregator/
│   │   ├── config.py              # Stores, categories, keywords, model names, brands
│   │   ├── browser.py             # Playwright browser scraping (JS-rendered sites)
│   │   ├── categorizer.py         # Product categorization engine
│   │   ├── db.py                  # SQLite queries (deals, aggregation)
│   │   ├── auth_db.py             # Turso auth DB (invite codes, sessions, events, waitlist)
│   │   ├── auth.py                # JWT middleware, invite validation
│   │   ├── scraper.py             # Multi-store scraper orchestrator
│   │   ├── reviews.py             # Review score matching
│   │   ├── models.py              # Data models
│   │   ├── cli.py                 # Admin CLI (scrape, generate-codes, sync)
│   │   ├── wordlist.py            # Snow-themed words for invite codes
│   │   ├── web/
│   │   │   ├── app.py             # FastAPI app factory
│   │   │   ├── routes.py          # Main routes (/, /deals, /status)
│   │   │   ├── invite_routes.py   # Landing page, invite validation, waitlist
│   │   │   ├── admin_routes.py    # Admin panel (codes, stats)
│   │   │   ├── event_routes.py    # Click/event tracking API
│   │   │   ├── templates/         # Jinja2 templates
│   │   │   │   ├── index.html     # Main deal page (filters, presets, grid)
│   │   │   │   ├── invite.html    # Marketing landing page
│   │   │   │   ├── status.html    # Store health dashboard
│   │   │   │   └── partials/      # Card, grid, pagination partials
│   │   │   └── static/
│   │   │       ├── style.css      # All styles (~1500 lines, CSS variables)
│   │   │       └── img/           # Favicon, hero-bg, empty-state
│   │   └── parsers/               # Per-store scrapers
│   └── tests/
├── tampermonkey/                   # Browser userscript (secondary)
├── snow_deals/                     # Python CLI (secondary)
├── GTM.md                          # Go-to-market strategy
├── .github/workflows/scrape.yml   # Cron scraper (every 6h)
└── Dockerfile
```

## Development Workflow

```bash
# Setup
cd aggregator && pip install -e .

# Run locally
uvicorn aggregator.web.app:create_app --factory --reload

# Run tests
python -m pytest aggregator/tests/ -x -q

# Manual scrape
python -m aggregator.cli scrape

# Generate invite codes
python -m aggregator.cli generate-codes --count 5
```

## Coding Conventions

- **Templates:** Jinja2 + htmx for interactivity, no JS frameworks
- **CSS:** Custom properties (CSS variables), dark theme only, Inter font
- **JavaScript:** Vanilla JS inline in templates, no build step
- **Python:** Type annotations on public functions, async/await throughout
- **Categorization:** Keyword-based in `config.py` — use space-padded keywords to avoid substring false positives (e.g., `" used "` not `"used"`)
- **Model names:** Ambiguous single-word model names go in brand-qualified `MULTI_WORD_MODEL_NAMES`, not generic sets
- **htmx patterns:** `hx-get="/deals"`, `hx-target="#deal-grid"`, `hx-include=".filters [name]"` for filter syncing

## Architecture Decisions

- **Invite-gated access:** Controlled growth via human-readable invite codes (`POWDER-SUMMIT-42`). Landing page is public for SEO/marketing, deal content requires authentication.
- **Server-rendered with htmx:** No SPA framework. Jinja2 templates + htmx partials give fast interactivity with minimal JS complexity. Cards render server-side, filters trigger htmx GETs.
- **SQLite + Turso split:** Deal data in local SQLite (fast reads, scraped every 6h). Auth/session/event data in Turso cloud DB (persistent across deploys).
- **Keyword-based categorization:** Products categorized by keyword matching against name/URL, with brand fallback. Not ML-based — fast, deterministic, debuggable. False positives fixed by expanding `NOT_HARDGOODS_KEYWORDS` or moving ambiguous model names.
- **GitHub Actions scraping:** Runs on cron, not on the web server. Keeps the web app stateless and fast. Scrape results committed to DB.
- **Repo is public** (changed 2026-05-17): Keep the project launch-friendly, but never commit secrets, cookies, credentials, auth databases, scraped `.db` files, or private operational tokens.
