# Ski Essentials exact-offer release

Replace the snow source's listing-only browser extraction with its publicly exposed collection feed. All six existing collections stay configured. The candidate yields 482 eligible products with 1,251 exact offers after excluding configurable bundle base prices and unsupported variants. Prices, references, stock, sizes and purchase links stay bound to one SKU. Default percentage-first ranking, history and other sources remain unchanged.

Evidence: `docs/benchmarks/2026-11-04-skiessentials-candidate.json`, 605 passing offline tests, and the exact CI lint command. Thirty independent product-page checks all match, including selected destinations; this does not prove checkout accuracy or historical selling prices. The source count reduction is explained by 424 configurable bundles and six unsupported offers, with six additions.

Under standing release approval: push this reviewed branch, merge after CI and preview checks pass, then dispatch the existing Scrape Deals workflow for `stores=Ski Essentials`, with reviews disabled. Preserve the restored public snapshot and history and all existing source/quality gates. Verify the new scrape timestamp, exact variant disclosure, available 178 cm versus unavailable 172 cm, percentage/budget filters and full/partial routes on production. Custom-host TLS currently fails locally but has passed on the GitHub runner; retain both observations.

If collection reconciliation, publication gates or live checks fail, retain the last verified snapshot and investigate. Revert this release through a normal reviewed commit to restore the prior browser adapter if needed; never force-push, erase history or renew timestamps on old observations.

Completed: PR #15 merged as `ad80035129ce3103bbd154c3b67efe9b583e3d58`; targeted workflow `41776930375` passed on that commit. Production 48-response traversal published 482 products / 1,250 variants, with no withheld source. Exact-option full/partial checks and all prior history rows passed. See `docs/benchmarks/2026-11-04-skiessentials-rollout.json` for live receipt and limitations.
