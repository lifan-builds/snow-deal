# Agent Guide

## Project Overview

**snow-deals aggregator** is a sub-project within the snow-deals monorepo that scrapes 13 ski and snowboard retailers, stores deal snapshots in SQLite, and serves a ranked deal dashboard via FastAPI + htmx. It uses Playwright headless browser for JS-rendered and anti-bot sites, httpx/BeautifulSoup for static sites, and reuses `ShopifyParser` and `BlueZoneParser` from the parent `snow_deals` package. Users interact through a Click CLI (scrape/query) or a browser-based UI with live filtering by category, store, discount, and tax-free status.

## Tech Stack

- **Language:** Python 3.11+
- **Web framework:** FastAPI >= 0.110, uvicorn >= 0.29
- **Templating:** Jinja2 >= 3.1, htmx 2.x (CDN, no build step)
- **Database:** SQLite via aiosqlite >= 0.20
- **HTTP client:** httpx >= 0.27 (async)
- **Browser automation:** Playwright (headless Chromium with anti-bot stealth)
- **HTML parsing:** BeautifulSoup4 >= 4.12, lxml >= 5.0
- **CLI:** Click >= 8.1
- **Terminal output:** Rich >= 13.0
- **Parent dependency:** `snow_deals` package (ShopifyParser, BlueZoneParser, Product model)

## Project Structure

```
aggregator/
├── pyproject.toml               # Package metadata and dependencies
├── AGENTS.md                    # This file — AI agent instructions
├── PLANS.md                     # Living execution plan
├── README.md                    # Human-oriented project README
├── deals.db                     # SQLite database (gitignored)
├── aggregator/
│   ├── __init__.py
│   ├── config.py                # Store registry (13 stores), category keywords, tax_free flags
│   ├── models.py                # AggregatedDeal dataclass
│   ├── categorizer.py           # Keyword-based product → category mapping
│   ├── db.py                    # SQLite schema, init, upsert, query, store_status
│   ├── scraper.py               # Multi-store async orchestrator with rate limiting
│   ├── browser.py               # Playwright-based scraper with per-store JS extractors
│   ├── cli.py                   # Click CLI (refresh, deals)
│   ├── parsers/
│   │   ├── __init__.py          # Extended parser registry
│   │   ├── evo.py
│   │   ├── backcountry.py
│   │   └── rei.py
│   └── web/
│       ├── __init__.py
│       ├── app.py               # FastAPI app factory
│       ├── routes.py            # Page + htmx partial + status dashboard routes
│       ├── templates/
│       │   ├── index.html       # Main deals page with filters
│       │   ├── status.html      # Store status dashboard
│       │   └── partials/
│       │       └── deal_cards.html  # htmx partial for deal grid
│       └── static/
│           └── style.css        # Dark-theme CSS
```

## Development Workflow

```bash
# From the aggregator/ directory
python -m venv .venv && source .venv/bin/activate

# Install parent package first (from repo root)
pip install -e ..

# Install aggregator
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Scrape all stores and populate SQLite
snow-deals-agg refresh

# Query deals from the database
snow-deals-agg deals --min-discount 20 --category skis

# Run the web UI
uvicorn aggregator.web.app:create_app --factory --reload
# Main page: http://localhost:8000/
# Status dashboard: http://localhost:8000/status
```

## Coding Conventions

- **Async throughout:** All I/O (HTTP, SQLite, Playwright) uses async/await.
- **Dataclasses for models:** `AggregatedDeal` wraps `snow_deals.Product` with store/category metadata.
- **Parser inheritance:** New parsers inherit `BaseParser` from `snow_deals.parsers.base`.
- **Rate limiting:** Per-domain semaphores in `scraper.py` to avoid hammering retailers.
- **htmx for interactivity:** No JavaScript build step. Dynamic filtering via htmx partials.
- **Type-annotate all public functions.**
- **Browser scraping:** Store-specific JS extractors in `browser.py` use `page.evaluate()`. Use `forEach` over `for...of` for NodeList iteration. Use `domcontentloaded` (not `networkidle`) for anti-bot sites.

## Architecture Decisions

- **SQLite for persistence:** Avoids re-scraping on every page load. Deals are snapshots refreshed via CLI.
- **Keyword-based categorization:** Product titles and URLs are matched against keyword lists in `config.py`. Shopify collection handles provide strong category signals.
- **Concurrent scraping with `asyncio.gather`:** Each store is scraped in parallel, with per-domain semaphores for rate limiting.
- **Playwright for JS-rendered sites:** Evo, Backcountry, Steep & Cheap, Level Nine Sports, Corbetts, Alpine Shop VT, The Circle Whistler, The House all require headless browser with anti-bot stealth measures.
- **htmx frontend:** Server-rendered HTML with htmx for dynamic filtering. No build tooling, no client-side framework.
- **Reuse parent parsers:** Shopify and BlueZone parsers are imported from `snow_deals` rather than duplicated.
- **Tax-free tagging:** Canadian stores (PRFO, The Circle Whistler, Corbetts) are marked `tax_free=True` in config for UI display.
- **Separate status dashboard:** Store health/freshness is shown on a dedicated `/status` page with summary stats, freshness legend, and per-store table.
- **Powder7 removed:** Site primarily sells used gear — excluded from scraping.
