# Prepared Fresh Powder release

Destination repository: `lifan-builds/snow-deal` (public). Application: https://freshpowder.clifan.com/. Local release branch: `codex/deal-aggregator-release`, based on production `a0a611b`.

## Proposed change

**Title:** Extract Deal Aggregator workspace and preserve size-specific bargain prices

**Description:** Fresh Powder previously summarized one price per product, so another size's price could not participate in filtering and ranking. This release retains eligible variant offers and selects the matching offer before counts, ordering, and pagination. Cards keep price, reference, size, stock evidence, and merchant destination consistent. Default ordering remains deepest percentage discount first.

Shared ingestion, parser utilities, offer models, and throttling move into `common/`; the existing snow application, tests, and deployment assets move into `catalogs/fresh-powder/`. Root deployment adapters continue serving Fresh Powder. Optional original-price and model-year filters, compact offer cards, and browser-local saved searches improve the shopping path. The refresh report exposes variant and confirmed-size coverage.

**Validation:** 237 Python tests, 2 JavaScript tests, targeted lint and syntax checks, browser size/year/save/restore flows, package checks, and a bounded real Aspen feed/merchant check. No full refreshed variant snapshot has been published. Retailer reference prices remain unverified historical selling prices; stock is a merchant report, not a checkout guarantee.

## Proposed publication actions

1. Push this release branch to the existing public repository, create a PR with the title/description above, inspect CI, and merge the reviewed change into `main` if checks pass.
2. Run the existing full `Scrape Deals` workflow after merge. It restores prior history, validates the new parser/tests, requires at least 20 reliable sources and existing completeness/category gates, and publishes the snapshot to the existing `lifan-builds/snow-deal-data` release only if those gates pass.
3. Let the existing Vercel integration/deploy hook update https://freshpowder.clifan.com/. A merge may start a Vercel build before the refreshed snapshot exists; schema migration permits browsing, but exact-size coverage may be limited during that interval. Do not claim full variant coverage until the refresh report and live checks support it.
4. Verify production snapshot identity, size/year filters, counts, merchant links, and mobile layout. If validation fails, investigate without bypassing the gates; restore the prior app/snapshot pair if needed.

The scope excludes unrelated tooling edits, credentials, browser/auth state, existing local databases, private research-chat evidence, outreach, email delivery, and cycling deployment. Original local edits are preserved. This plan has not been executed externally; publication awaits the user's approval.

## Remaining product validation

- Complete a representative merchant audit; the two observed products do not establish the proposed 95-of-100 target.
- Validate shoppers' find-and-understand task success and voluntary repeat use.
- Review a manual exceptional-find pilot with approved recipients before email delivery.
- Add structured condition/restriction evidence and extend category coverage only where source data supports it. Existing used/demo exclusions remain unchanged; no unsupported condition selector was added.
- Keep cycling research-only until the snow quality and audience process is repeatable.
