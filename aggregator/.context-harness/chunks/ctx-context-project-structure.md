# Project Structure


```
aggregator/
├── pyproject.toml               # Package metadata and dependencies
├── AGENTS.md                    # This file — AI agent instructions
├── PLANS.md                     # Living execution plan
├── README.md                    # Human-oriented project README
├── deals.db                     # SQLite database (gitignored)
├── aggregator/
│   ├── __init__.py
│   ├── config.py                # Store registry (24 stores), category keywords, exclude keywords, brand/model/boot name sets, multi-word model names, tax_free flags
│   ├── models.py                # AggregatedDeal dataclass (sizes, length_min/max, image_url, brand, review_score/award/url)
│   ├── categorizer.py           # Keyword + brand-based product → category mapping with boot disambiguation and exclusion filter
│   ├── db.py                    # SQLite schema (deals, reviews, deal_reviews), CRUD, migrations, get_category_counts
│   ├── auth_db.py               # Turso cloud SQLite for auth (invite_codes, sessions, events) — local SQLite fallback for dev
│   ├── scraper.py               # Multi-store async orchestrator with dynamic parser registry, sizes cleaning, length extraction
│   ├── reviews.py               # OGL + TGR review scrapers, two-pass fuzzy matcher, model-to-brand lookup, compute_and_store_deal_reviews()
│   ├── browser.py               # Playwright-based scraper with per-store JS extractors (9 stores, extracts name/url/prices/image_url)
│   ├── cli.py                   # Click CLI (refresh, deals, fetch-reviews, generate-codes, list-codes)
│   ├── auth.py                  # JWT session auth middleware + admin bypass via ADMIN_KEY env var (no DB lookup for session validation)
│   ├── parsers/
│   │   ├── __init__.py          # Parser registry docs
│   │   ├── common.py            # Shared parse_price() used by all BS4 parsers
│   │   ├── alpineshopvt.py      # Alpine Shop VT (BigCommerce)
│   │   ├── thecircle.py         # The Circle Whistler (Lightspeed eCom)
│   │   ├── coloradodiscount.py  # Colorado Discount Skis (custom HTML)
│   │   └── sacredride.py        # Sacred Ride (WooCommerce)
│   └── web/
│       ├── __init__.py
│       ├── app.py               # FastAPI app factory (lifespan init_db, auth middleware, all routers)
│       ├── routes.py            # Page + htmx partial + status routes; uses pre-joined deal_reviews, no runtime fuzzy matching
│       ├── invite_routes.py     # GET/POST /invite for invite code entry
│       ├── admin_routes.py      # GET/POST /admin/codes for invite code management
│       ├── event_routes.py      # POST /api/event (analytics tracking) + GET /admin/stats (dashboard)
│       ├── templates/
│       │   ├── index.html       # Main deals page with sticky toolbar, filters (search, category, brand, store, sort, length range, reviewed, tax-free) + analytics JS
│       │   ├── invite.html      # Invite code entry page (dark-themed)
│       │   ├── status.html      # Store status dashboard
│       │   ├── admin_codes.html # Admin invite code management page
│       │   ├── admin_stats.html # Admin analytics dashboard (KPIs, charts, tables)
│       │   └── partials/
│       │       ├── _card.html       # Shared deal card markup: image, discount badge, review score (from deal.review_score)
│       │       ├── deal_cards.html  # htmx partial for deal grid (initial load)
│       │       └── more_cards.html  # htmx partial for load-more pagination
│       └── static/
│           └── style.css        # Glassmorphism dark theme with gradient accents, glow effects, sticky toolbar
├── tests/
│   ├── test_parse_price.py      # Shared price parser tests
│   ├── test_categorizer.py      # Keyword categorization tests
│   ├── test_reviews.py          # Brand extraction + fuzzy matching tests
│   ├── test_parsers.py          # BS4 parser tests (AlpineShopVT, ColoradoDiscount, SacredRide)
│   ├── test_db.py               # SQLite CRUD, filters, upsert, brand query tests
│   ├── test_browser_config.py   # Store config registry + raw product parsing tests
│   ├── test_scraper.py          # Kids filter + product-to-deal conversion tests
│   └── test_web_routes.py       # Web auth/public-mode/rate-limit route tests
```
