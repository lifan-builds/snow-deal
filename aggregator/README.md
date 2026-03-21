# snow-deals aggregator

Multi-store deal aggregator for ski and snowboard gear. Scrapes 13 retailers, stores deal snapshots in SQLite, and serves a ranked dashboard via FastAPI + htmx. Part of the [snow-deals](../) monorepo.

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

#### Query deals from the CLI

```bash
# Top deals across all stores
snow-deals-agg deals

# Filter by category and minimum discount
snow-deals-agg deals --category skis --min-discount 20

# Filter by store
snow-deals-agg deals --store "Evo" --limit 25
```

#### Web UI

```bash
uvicorn aggregator.web.app:create_app --factory --reload
# Open http://localhost:8000
```

The web UI provides:
- Live filtering by category, store, and discount percentage via htmx
- Sort by discount, price, store, or newest
- Tax-free indicators for Canadian stores
- Store status dashboard at `/status` with data freshness indicators

## Development

```bash
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## Project Structure

```
aggregator/
├── aggregator/
│   ├── config.py          # Store registry, category keywords, tax-free flags
│   ├── models.py          # AggregatedDeal dataclass
│   ├── categorizer.py     # Keyword-based product categorization
│   ├── db.py              # SQLite schema, CRUD, store status queries
│   ├── scraper.py         # Multi-store async scraper
│   ├── browser.py         # Playwright headless browser with per-store JS extractors
│   ├── cli.py             # Click CLI (refresh, deals)
│   ├── parsers/           # Store-specific parsers
│   └── web/               # FastAPI app with htmx templates + status dashboard
├── pyproject.toml
└── README.md
```

## Supported Stores

| Store | Type | Tax Free | Status |
|-------|------|----------|--------|
| Aspen Ski and Board | Shopify | No | Active |
| PRFO | Shopify | Yes | Active |
| Sports Basement | Shopify | No | Active |
| BlueZone Sports | BS4 | No | Active |
| Alpine Shop VT | Playwright (BigCommerce) | No | Active |
| The Circle Whistler | Playwright (Lightspeed) | Yes | Active |
| Colorado Discount Skis | httpx | No | Active |
| Evo | Playwright | No | Active |
| Backcountry | Playwright (Chakra UI) | No | Active |
| Steep & Cheap | Playwright (Chakra UI) | No | Active |
| The House | Playwright (GTM) | No | Active |
| Corbetts | Playwright (BigCommerce) | Yes | Active |
| Level Nine Sports | Playwright (Chakra UI) | No | Active |

## License

MIT
