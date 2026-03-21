# snow-deals aggregator — Execution Plan

This is a living document. Keep Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective up to date as work proceeds.

## Purpose / Big Picture

A user can run `snow-deals-agg refresh` to scrape deals from 13 ski/snowboard retailers into a local SQLite database, then browse a FastAPI + htmx web UI to filter and rank deals by category, store, discount percentage, and tax-free status. A CLI is also available for terminal-based querying. A separate status dashboard shows store health and data freshness.

## Progress

### Phase 1: Bootstrap (Complete)
- [x] Scaffold aggregator directory structure
- [x] Create pyproject.toml with dependencies
- [x] Implement store registry and category keywords (config.py)
- [x] Implement AggregatedDeal model (models.py)
- [x] Implement keyword categorizer (categorizer.py)
- [x] Implement SQLite schema and CRUD (db.py)
- [x] Implement multi-store async scraper (scraper.py)
- [x] Implement Click CLI with refresh and deals commands (cli.py)
- [x] Implement FastAPI app with htmx templates (web/)
- [x] Create project documentation (AGENTS.md, PLANS.md, README.md)

### Phase 2: Store Parsers & Browser Scraping (Complete)
- [x] Implement Playwright-based browser scraper (browser.py) with anti-bot stealth
- [x] Implement all 14 store-specific JS extractors
- [x] Fix Backcountry Chakra UI extractor (`.chakra-linkbox .price`)
- [x] Fix Steep & Cheap URL paths (`/cat/` not `/rc/`)
- [x] Fix Level Nine Sports (shares Backcountry parser, anti-bot handling)
- [x] Fix Corbetts BigCommerce price selectors and dedup
- [x] Fix Evo price selectors (`.product-thumb-price.slash`)
- [x] Fix Alpine Shop VT BigCommerce price selectors
- [x] Fix The House GTM `percentOff` original price calculation
- [x] Fix The Circle Whistler Lightspeed data attributes + lazy-load timing
- [x] Fix Colorado Discount Skis URL (Rossignol.html)
- [x] Remove Powder7 (used items)
- [x] End-to-end scrape: 13 stores, ~3,700 deals, ~2,400 with discounts

### Phase 3: UI Features (Complete)
- [x] Sort control (discount, price low/high, store, newest)
- [x] Deal count display with htmx OOB updates
- [x] Category tags on deal cards
- [x] Remove product images from cards
- [x] Store status/freshness dashboard (separate `/status` page)
- [x] Tax-free tags on deal cards and status page
- [x] Header navigation between deals and status pages

### Phase 4: Enhancements (Upcoming)
- [ ] Tax-free filter toggle on deals page
- [ ] Verify Corbetts scrape completeness (key tax-free store)
- [ ] Pagination or infinite scroll for large result sets
- [ ] Automated scheduled scraping (cron or background task)

## Surprises & Discoveries

- Backcountry, Steep & Cheap, and Level Nine Sports all use the same Chakra UI component library — one extractor works for all three with parser_type aliasing.
- `networkidle` wait strategy causes timeouts on anti-bot sites; `domcontentloaded` + explicit delays is more reliable.
- The Circle Whistler (Lightspeed eCom) lazy-loads variant price attributes after initial render — needs 3s post-selector wait.
- `for...of` on NodeList silently fails in some Playwright `page.evaluate()` contexts — `forEach` is safer.
- Powder7 primarily sells used gear — removed from scraping to keep deal quality high.
- Corbetts uses BigCommerce with BODL data layer — `.price--withoutTax` and `.price--non-sale` selectors.

## Decision Log

- Decision: Use SQLite via aiosqlite instead of a full database server
  Rationale: Local-first tool, no need for concurrent writes. SQLite is zero-config and portable.
  Date: 2026-03-20

- Decision: htmx for frontend interactivity instead of React/Vue
  Rationale: No build step, minimal JS, server-rendered HTML. The filtering UI is simple enough that htmx partials cover all needs.
  Date: 2026-03-20

- Decision: Reuse ShopifyParser and BlueZoneParser from snow_deals
  Rationale: Several stores are Shopify-based and BlueZone already has a parser. Avoids code duplication.
  Date: 2026-03-20

- Decision: Per-domain semaphores for rate limiting
  Rationale: Scraping ~13 stores concurrently could overwhelm individual servers. Semaphores limit to 2 concurrent requests per domain.
  Date: 2026-03-20

- Decision: Playwright for JS-rendered stores with anti-bot stealth
  Rationale: 8+ stores require JavaScript rendering. Anti-bot measures (webdriver flag hiding) needed for Evo, Backcountry, Level Nine, Corbetts.
  Date: 2026-03-20

- Decision: Remove Powder7 from store registry
  Rationale: Site primarily sells used/consignment items, which don't represent genuine deals.
  Date: 2026-03-20

- Decision: Separate status dashboard at /status instead of inline panel
  Rationale: Keeps the main deals page clean while providing detailed store health information on a dedicated page.
  Date: 2026-03-20

- Decision: Mark Canadian stores as tax-free
  Rationale: PRFO, The Circle Whistler, and Corbetts are Canadian retailers that don't charge US sales tax, which is valuable deal information.
  Date: 2026-03-20

## Outcomes & Retrospective

Phases 1–3 complete. All 13 stores scrape successfully. Web UI is functional with filtering, sorting, tax-free indicators, and a separate status dashboard. Key remaining work: tax-free filter toggle, Corbetts scrape verification, and potential pagination.

## Context and Orientation

This is a sub-project within the snow-deals monorepo (`aggregator/` directory). It depends on the parent `snow_deals` package for `ShopifyParser`, `BlueZoneParser`, and the `Product` model. The aggregator adds multi-store orchestration, Playwright browser scraping, SQLite persistence, keyword categorization, and a web UI. Target retailers are sourced from uscardforum.com — Shopify-based stores use existing parsers; others use Playwright with store-specific JS extractors in `browser.py`.

## Plan of Work

Current focus is on Phase 4 enhancements — adding a tax-free filter toggle, verifying Corbetts scrape completeness, and potentially adding pagination for large result sets.

## Validation and Acceptance

- `pip install -e .` succeeds in the aggregator directory (with snow_deals installed).
- `snow-deals-agg refresh` scrapes all 13 stores and populates SQLite with ~3,700+ deals.
- `snow-deals-agg deals` displays a Rich table of deals from the database.
- `uvicorn aggregator.web.app:create_app --factory` starts the web UI on localhost:8000.
- Filtering by category, store, sort, and discount % works via htmx.
- `/status` page shows all 13 stores with freshness indicators.
- Tax-free tags appear on Canadian store deals.
