# FreshPowder

The best ski & snowboard deals, curated. FreshPowder tracks prices across 15+ North American retailers every 6 hours, matches expert review scores, and surfaces the best deals so you don't have to check every store.

**Live at:** https://snow-deals.onrender.com (invite-only)

## Features

- **Multi-store aggregation** — Tracks deals across evo, Backcountry, REI, Steep & Cheap, The House, and 10+ more stores
- **Expert reviews** — Matches products with OutdoorGearLab and GoodRide review scores
- **Smart filtering** — 10 filter types: category, brand, store, discount, price, length, reviewed, tax-free, search, sort
- **Quick presets** — One-tap filters: "Under $100", "Top Reviewed", "50%+ Off", "Tax Free", "New Arrivals"
- **Real-time search** — Search by brand, model, or keyword with term highlighting
- **Share deals** — Share button copies deal links or uses native share on mobile
- **Click analytics** — Track which deals and stores get the most engagement
- **Invite system** — Human-readable invite codes (POWDER-SUMMIT-42), controlled growth

## Tech Stack

- **Backend:** Python 3.12, FastAPI, aiosqlite
- **Frontend:** Jinja2, htmx, vanilla JS, custom CSS
- **Database:** SQLite (deals) + Turso (auth/events)
- **Scraping:** GitHub Actions cron, httpx, BeautifulSoup4
- **Deployment:** Docker on Render

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
cd aggregator
pip install -e .
```

### Run Locally

```bash
# Set required env vars
export SECRET_KEY="your-secret"
export ADMIN_KEY="your-admin-key"

# Start the dev server
uvicorn aggregator.web.app:create_app --factory --reload
```

### Run Tests

```bash
python -m pytest aggregator/tests/ -x -q
```

### Admin CLI

```bash
# Run a manual scrape
python -m aggregator.cli scrape

# Generate invite codes
python -m aggregator.cli generate-codes --count 5

# Sync auth DB to Turso
python -m aggregator.cli sync-auth
```

## Project Structure

```
├── aggregator/              # Main web app
│   ├── aggregator/
│   │   ├── config.py        # Store configs, categories, keywords
│   │   ├── categorizer.py   # Product categorization
│   │   ├── db.py            # Deal queries
│   │   ├── auth_db.py       # Auth database (Turso)
│   │   ├── scraper.py       # Multi-store scraper
│   │   ├── reviews.py       # Review score matching
│   │   ├── web/             # FastAPI web app
│   │   └── parsers/         # Per-store scrapers
│   └── tests/
├── tampermonkey/            # Browser userscript (secondary)
├── snow_deals/              # Python CLI (secondary)
├── GTM.md                   # Go-to-market strategy
├── .github/workflows/       # Scrape cron job
└── Dockerfile
```

## License

MIT
