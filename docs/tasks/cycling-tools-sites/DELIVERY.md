# Cycling and workshop tools — delivery record

## Built on November 2, 2026

| Catalog | Working name | Local preview | Default reference floor | Matching live listings |
| --- | --- | --- | ---: | ---: |
| Cycling | Big Ring | http://127.0.0.1:8766/ | $1,000 | 249 |
| Workshop/power tools | Bench Drop | http://127.0.0.1:8767/ | $200 | 71 |

Counts are from the dated [inventory check](inventory-check.json), not a promise of future stock. Cycling covers BikesOnline and Mike's Bikes; tools initially covers Woodcraft. Both show limited source coverage explicitly. The highest observed discounts were 73.5% and 50.4%, calculated from retailer references, not independently established historical prices.

## Implemented

- Shared `common/deal_common/catalog/` engine, with separate definitions, artwork, source lists, classifications, and databases in each catalog.
- Complete source replacement is atomic. Errors, malformed feeds, uncertain currency, or page caps preserve the preceding snapshot and its original timestamp. Full empty feeds remove previous offers. Observations are retained separately.
- Exact-size and stock eligibility are resolved before price/reference filtering, ranking, counts, and pagination. Default order is percentage off, then dollar savings. USD sources must pass the storefront currency check.
- Server-rendered responsive sites, search, category/brand/retailer/size/package/platform filters where relevant, reference floor, budget, minimum discount, source health, and browser-local saved searches.
- Preview pages are noindex. An explicit public URL enables canonical metadata, sitemap and robots discovery; query permutations remain noindex.
- Standalone deployment packager rejects missing, stale, incomplete, wrong-catalog or empty default snapshots. It copies only common code, the chosen catalog, and its configured source data. Root Fresh Powder deployment files are unchanged.
- Manual GitHub workflow prepares fresh deployable artifacts. It does not publish sites or activate a schedule.

## Verification

- 277 offline Python tests pass, including the full Fresh Powder regression suite. Four pre-existing warnings concern old datetime calls and a fixture signing key.
- Ruff passes for the new runtime, definitions, tests and packager. JavaScript syntax check passes.
- Both standalone bundles are served in offline tests; assets, public/noindex metadata, catalog isolation and stale-build rejection are covered.
- Browser checks cover desktop/mobile layout at 390px without horizontal overflow, mobile filter disclosure, exact-size selection, a two-result kit query, saving a search, and source coverage. Both previews have no browser console errors. Local real inventory is used; test fixtures are never presented as merchant listings.
- Wheel packaging includes both new Python packages, templates, CSS, JavaScript, and catalog SVG assets. No database or credential files belong in the wheel.

## Reproduce

Install once from root with `pip install -e '.[dev]'`. See each catalog README for refresh and serve commands. In this checkout, the existing environment at `/Users/lfan/Project/fresh-powder/.venv/bin/python` is used with `PYTHONPATH=common:catalogs/cycling/src:catalogs/tools/src` for previews; existing dependencies and operational databases were not relocated.

Task-owned local data, screenshots and standalone builds are in `.local/catalog-preview/`, excluded from Git. Latest prepared bundles are `bigring-final/` and `benchdrop-final/` inside that directory. To prepare a separate deploy directory:

```bash
python scripts/package_catalog.py cycling --database catalogs/cycling/data/catalog.db --output .local/catalog-preview/bigring-build
python scripts/package_catalog.py tools --database catalogs/tools/data/catalog.db --output .local/catalog-preview/benchdrop-build
```

Choose a new output directory for each build. Inspect `BUILD-RECEIPT.json` before deploying. Each directory contains its own Vercel config and function. Keep the repo root's Vercel project pointed at Fresh Powder.

## Public launch remains separate

No push, PR, Vercel deployment, DNS change, or recurring job activation was performed for these new sites. Suggested destinations for review are `bigring.clifan.com` and `benchdrop.clifan.com`; they have not been provisioned or claimed. The prior Fresh Powder release approval was specific to that release.

After publication approval: create two independent Vercel projects, regenerate each bundle with the approved `--public-url https://...`, deploy it, attach only the approved subdomains, and verify live data and routing. Configure refresh plus redeploy at least daily; scheduled refresh alone cannot update an immutable deployment snapshot. Preserve the existing apex/mail DNS and Fresh Powder project. The manual artifact workflow can prepare snapshots now, but a recurring production deployment must be wired to the approved projects before launch is considered operational.

## Practical limits

- Tools has one verified retailer so far. Factory Authorized Outlet had no valid discounts, MaxTool hit its page cap, and Red Tool Store's currency request failed. These are research outcomes, not enabled inventory sources.
- Discount reference accuracy and stock have not been independently audited at checkout. Condition exclusions use titles and retailer taxonomy; unmarked used/open-box conditions can require a merchant adapter.
- Cycling size strings can include wheel size. No geometry fit, component compatibility, or model-year inference is invented.
- Tools package/platform labels use explicit title evidence. Unknown package content remains unknown; batteries, shipping, taxes, coupons, financing and returns are not silently priced in.
- Source observations are retained, but consumer-facing historical-low claims and email alerts are not implemented.
