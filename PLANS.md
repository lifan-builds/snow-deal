# Deal — Bootstrap & Tampermonkey Pivot

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must stay up to date as work proceeds.

## Purpose / Big Picture

After this work, a user can install a Tampermonkey userscript and browse BlueZone Sports product listing pages to see discount-percentage badges on every product card, with a one-click button to sort the grid by best deal. A secondary Python CLI is available for bulk data export.

## Progress

- [x] (2026-03-13) Create project documentation (AGENTS.md, PLANS.md, README.md)
- [x] (2026-03-13) Create pyproject.toml with dependency definitions
- [x] (2026-03-13) Implement Product data model with discount calculation
- [x] (2026-03-13) Implement base parser interface
- [x] (2026-03-13) Implement BlueZone Sports parser (product extraction + pagination)
- [x] (2026-03-13) Implement async scraper orchestrator
- [x] (2026-03-13) Implement display module (rich table, CSV, JSON output)
- [x] (2026-03-13) Implement CLI entry point
- [x] (2026-03-13) End-to-end test against live BlueZone Sports URL — scraped 216 products across 9 pages, 155 on sale
- [x] (2026-03-13) Pivot to Tampermonkey userscript as primary interface
- [x] (2026-03-13) Create deal.user.js — badge injection, sort button, price extraction ported from Python parser
- [x] (2026-03-13) Update project docs (AGENTS.md, PLANS.md, README.md) for userscript-first approach

## Surprises & Discoveries

- Observation: BlueZone Sports has 9 pages of skis (216 products), not 5 as shown in the visible pagination.
  Evidence: The "1 / 5" shown in the UI is misleading; the Next button continues beyond page 5.
- Observation: BlueZone uses `aria-label="Next"` for pagination, not `rel="next"`.
  Evidence: HTML inspection of the pagination nav element.

## Decision Log

- Decision: Use httpx async instead of requests
  Rationale: Enables concurrent pagination fetches and is more modern; httpx has a nearly identical API to requests for easy migration.
  Date/Author: 2026-03-13

- Decision: Plugin-based parser architecture from day one
  Rationale: Different e-commerce sites have vastly different HTML structures. Isolating site-specific logic in parser modules makes the tool extensible without modifying core code.
  Date/Author: 2026-03-13

- Decision: Use BeautifulSoup4 with lxml for HTML parsing
  Rationale: lxml is fast and handles malformed HTML well. BS4 provides a clean API for navigating the DOM.
  Date/Author: 2026-03-13

- Decision: Pivot from CLI-only to Tampermonkey userscript as primary interface
  Rationale: Users are already browsing the site — injecting discount badges directly on the page is better UX than switching to a terminal. The CLI remains as a secondary tool for bulk data export.
  Date/Author: 2026-03-13

- Decision: Color-coded badge thresholds (30%+ red, 15-29% orange, 1-14% yellow)
  Rationale: Three tiers provide quick visual scanning without overwhelming the page. Full-price items get no badge to reduce noise.
  Date/Author: 2026-03-13

## Outcomes & Retrospective

MVP complete. Two interfaces available: Tampermonkey userscript (primary, in-browser) and Python CLI (secondary, bulk export). Both share the same proven CSS selectors for BlueZone Sports.

## Context and Orientation

This is a greenfield Python project. The target use case is finding the best discount deals on e-commerce sites like BlueZone Sports (https://www.bluezonesports.com/skis). Products on these sites display a current price and sometimes a strikethrough original price when on sale. The tool needs to scrape all paginated product listings, identify items with discounts, compute `(original - sale) / original * 100`, and present a ranked list.

## Plan of Work

1. **Data model** (`deal/models.py`): Define a `Product` dataclass with fields for name, url, current_price, original_price, and a computed `discount_pct` property.

2. **Parser interface** (`deal/parsers/base.py`): Define `BaseParser` ABC with methods: `parse_listing_page(html) -> list[Product]` and `get_next_page_url(html, current_url) -> str | None`.

3. **BlueZone parser** (`deal/parsers/bluezone.py`): Implement concrete parser. Extract product name, current price, original (strikethrough) price from product cards. Handle pagination links.

4. **Parser registry** (`deal/parsers/__init__.py`): Map URL domain patterns to parser classes. Provide a `get_parser(url) -> BaseParser` function.

5. **Scraper** (`deal/scraper.py`): Async function that takes a URL, resolves the right parser, fetches pages sequentially (with delay), parses products, follows pagination, and returns a full product list.

6. **Display** (`deal/display.py`): Format products as a Rich table (default), CSV, or JSON. Sort by discount percentage descending.

7. **CLI** (`deal/cli.py`): Click-based CLI with arguments for URL, output format, minimum discount filter, and delay between requests.

## Validation and Acceptance

- `deal https://www.bluezonesports.com/skis` produces a table of products sorted by discount %.
- Products with no discount are listed at the bottom (0% discount).
- `--format csv` and `--format json` produce valid output.
- `--min-discount 10` filters out products with less than 10% discount.
- The tool handles pagination (all 5 pages on the BlueZone skis listing).

## Idempotence and Recovery

The tool is read-only (no state, no database). Re-running the same command produces fresh results from the live site. Safe to retry at any time.

## Interfaces and Dependencies

```
deal/models.py:
  @dataclass Product(name, url, current_price, original_price, image_url)
    @property discount_pct -> float

deal/parsers/base.py:
  ABC BaseParser
    parse_listing_page(html: str) -> list[Product]
    get_next_page_url(html: str, current_url: str) -> str | None

deal/parsers/__init__.py:
  get_parser(url: str) -> BaseParser

deal/scraper.py:
  async scrape(url: str, delay: float = 1.0) -> list[Product]

deal/display.py:
  display_table(products: list[Product], min_discount: float = 0)
  export_csv(products: list[Product], path: str)
  export_json(products: list[Product], path: str)

deal/cli.py:
  cli() — Click group entry point
```
