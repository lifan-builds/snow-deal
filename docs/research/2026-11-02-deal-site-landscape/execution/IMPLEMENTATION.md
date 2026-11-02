# Fresh Powder: first execution milestone

Implemented locally on November 2, 2026. Target for a later approved rollout: https://freshpowder.clifan.com/. Screenshots use synthetic examples, not verified retailer inventory.

## Delivered

The workspace now shares product/offer models, Shopify parsing, HTTP traversal, and rate limiting in `common/`. Fresh Powder owns the snow taxonomy, persistence, retailer configuration, and branded UI in `catalogs/fresh-powder/`. Cycling remains a proposal.

The current production source at `a0a611b` was reconciled into this layout. This corrects an earlier checkout-based assessment: production already protected freshness at 72 hours and tied listed sizes to one displayed price. The improvement here retains all eligible discounted variants, so choosing another size can select another price instead of losing that product.

Each selected offer carries its price, retailer reference, size/options, availability, image, and destination. Selection happens before counting and percent-first ordering. Exact-size requests require reported in-stock availability. Unknown stock remains labeled when browsing without an exact size. Discrete length matching never fills gaps between listed lengths. Existing suspicious-discount limits remain in force.

Variant observations preserve dated prices, currency, and product identity. They cover parsed discounted offers, not comprehensive inventory history. They do not establish an all-time low or validate a retailer's original-price claim.

The UI puts gear, size, and minimum discount first. Cards show savings against the retailer reference, model year when explicit in the title, source check time, and a direct variant link. An original-price floor supports expensive-item discovery. Saved searches persist locally in the browser; no alert emails are sent.

## Verification

- Python suite: 234 passing tests, including matching-size price/link consistency, unknown/sold-out handling, budget-dependent offer selection, exact lengths, per-variant history, reused-product identity, pagination, and full-page/partial rendering. Four existing warnings remain.
- JavaScript analytics suite: 2 passing tests.
- Targeted Ruff check and `git diff --check`: pass.
- Wheel: shared and catalog packages, comparison data, templates, and JavaScript included; databases and tests excluded.
- Browser: 180 cm yields two synthetic offers at $320 and $350; 160 cm selects different variant prices and ordering; 175 cm produces no matches. Saved search survives reload and restores the 180 cm results.
- Responsive checks: 390 px mobile and 1280 px desktop. Evidence: [mobile](mobile-preview.png), [desktop](desktop-preview.png).

Run `.venv/bin/python scripts/preview_offers.py` from the repository root for the temporary local preview at http://127.0.0.1:8765. It creates disposable deal/auth databases and clears inherited service configuration.

## Follow-up verification

The model-year filter now lets shoppers request a minimum title-stated year; undated offers are excluded only when that filter is active. No default age restriction changes discount ranking. Browser verification returned the 2025 example and excluded the 2024 example, with the count and selected-filter chip agreeing. See [year filter](year-filter-preview.png).

Refresh reports now include variant counts, products with variants, and products with a reported in-stock size, both for fetched data and the candidate set after partial-source protection. These are feed-coverage metrics, not checkout-accuracy measurements. MSRP metadata is no longer displayed as a selectable size/color option.

Current verification: **237 Python tests and 2 JavaScript tests pass**, including a real merchant-feed fixture, year-filter count/results, and coverage semantics. The release checkout starts from the verified current public revision `a0a611bd489ee0f13a0ceded32b56ae91128cc10`; its unrelated tooling files are unchanged. The original working directory remains intact.

## Live-data evidence and limits

The initial HTTP probes for Aspen Ski and Board, The Startingate, and Freeride Boardshop returned HTTP 429. See [public-feed-audit.json](public-feed-audit.json). Those direct HTTP requests were not retried. Ordinary browser navigation subsequently reached Aspen's public JSON feed and merchant pages without a challenge or login.

The captured first collection page contains 24 products: 13 discounted products parsed, 11 passed the snow catalog rules, and 42 variants were retained. All 11 eligible products had a size reported in stock. This is one incomplete collection page, not a publishable store snapshot. See [sample report](aspen-sample-report.json) and [captured price/variant facts](aspen-skis-page-1.json).

The leading parsed Atomic Maverick 78 offer's direct variant URL selected 146 cm on the merchant page at $329.95 versus its $550 reference, with an enabled Add to cart button. A separate existing Fresh Powder listing for Dalbello DS Asolo 115 boots matched the merchant's $198.94/$950 prices; merchant-provided structured details reported both 23.5 and 24.5 variants available. Return terms state a 14-day window, unused condition/tags/original packaging, and buyer-paid return shipping. See [merchant observation](aspen-merchant-observation.json). No cart, payment, or checkout action occurred.

These spot checks prove only the observed facts for these products at that time. They do not establish the proposed 95-of-100 accuracy target, full inventory coverage, historical street prices, or future availability. The other two feeds remain unverified.

## Rollout sequence

1. Prepare a separate snapshot with the new schema and a successful fresh scrape through the existing supported scraper workflow. Keep the prior release snapshot available. Do not overwrite the running snapshot with rate-limited or incomplete results.
2. Measure confirmed size coverage, inspect a sample of variant links and prices on merchant pages, and check source freshness/completeness. HTML-only sources may still have unknown stock; they cannot satisfy exact-size filters without variant evidence.
3. Review the exact release for the existing Fresh Powder site and obtain publication approval under the user's standing preference. Deploy the app together with the validated snapshot. A normal download build adds schema, but migration alone cannot populate variants. A skip-download build requires an already prepared database.
4. Verify live filters, pagination, links, and mobile layout. Roll back the application and paired snapshot to the prior release if those checks fail.
5. Run the proposed snow-catalog user pilot before expanding to cycling. Recruitment, automated alerts, and additional categories remain separate work; none were represented as completed here.
