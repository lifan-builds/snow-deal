# Verification — 2 November 2026

## Automated checks

- `python scripts/check.py -q`: **287 passed**. Four existing warnings: three deprecated UTC datetime calls and one short JWT key in a fixture. The runner isolates temporary databases and inherited service secrets.
- Scoped Ruff checks passed for the new catalog runtime, benchmark, tests, cycling package and packaging/audit scripts.
- `node --check common/deal_common/catalog/static/catalog.js` and `git diff --check` passed.
- `scripts/benchmark.py ... --require-lead` returned **1 as intended**: the evidence does not support an all-metrics market-lead claim.
- Standalone Big Ring and Bench Drop packages rebuilt successfully under the ignored task preview directory. A subprocess test serves the isolated bundle and confirms multiple observation days survive packaging.

Regression cases include price/size selection before ranking/counting/pagination; stale and failed refresh handling; mismatched catalog identity; wrong product/variant destinations; frame versus wheel size; missing dimension metadata; accessory taxonomy before frameset keywords; clearing a default reference floor; preserving other filters; and price history isolation across dates, builds, options, variants and failed refreshes. Benchmark tests reject claims, missing evidence, incompatible cohorts, stale dates, non-finite values, local-vs-production speed comparisons, insufficient coverage margins and unsupported sampled-accuracy superiority.

## Browser checks

Used the in-app browser through CUA, with explicit 390×844 and 1280×900 viewports. No production forms, signups or external submissions were made.

- Big Ring: first price bottom 1,358.7 px before and 783.1 after with the same one saved-search chip; 727.1 after removing the test-created saved search. No horizontal page overflow. 24 rendered cards / 24 evidence disclosures. Desktop 1280 px has no overflow.
- Bench Drop: first price bottom 1,350.7 px before and 738.3 after; no horizontal page overflow. 24/24 cards expose a numeric retailer reference, explicit variant and observed timestamp. Expanded evidence and followed the first variant's history link: one real observed day, truthful insufficient-history wording, no mixed variants, no page overflow.
- Cycling exact M filter applied through visible controls: 104 matches, first card M / Black, selected purchase variant preserved; no wheel-size strings remain in the frame-size menu. Earlier 98 and later 104 counts involve different live snapshots, so the entire increase is not attributed to the parser fix.
- Fresh Powder synthetic preview: six offer-evidence disclosures, no horizontal overflow. Synthetic inventory is excluded from competitor coverage metrics.
- Fresh Powder production: first price bottom 806.9 px, default 7,792-result count observed. This is a broad catalog count, not qualified M1 coverage. No changes deployed in this iteration.
- Powder Deals: first price bottom 1,180.2 px; Velo Bargains 1,056.7 px; Daily Tool Drops 504.5 px. Default banners were retained. These are single layout observations, not network-performance or conversion studies.

Screenshots (local task artifacts, not committed):
- `.local/catalog-preview/benchmark-cycling-before.png`
- `.local/catalog-preview/benchmark-cycling-after.png`
- `.local/catalog-preview/benchmark-cycling-desktop.png`
- `.local/catalog-preview/benchmark-tools-after.png`

## Boundaries and remaining gaps

The cycling refresh completed against both configured retailers. A separate Red Tool Store probe returned `currency_check_failed`; the source was not enabled. Tool inventory remains Woodcraft-only. The shared source snapshots contain fewer than 30 distinct observation days. Neither a representative independent merchant accuracy audit across all competitors nor a comparable production LCP study has been completed. Provider capability claims and search-cache totals are labeled separately from current browser observations.

The work remains local on `codex/cycling-tools-sites`. Existing uncommitted site work was preserved. No push, deploy, DNS change, email delivery or new recurring automation was performed. The task's universal market-lead objective remains open; the research baseline, executable gate and this improvement batch are complete.

## Gap-closing continuation (latest)

307 offline tests pass after source expansion, explicit manufacturer normalization, 24-hour expiry, daily history retention, restoration/bootstrap checks, merchant audit and deployment fingerprint checks. Scoped Ruff, JS syntax, Ruby YAML parsing and diff whitespace checks pass. Both real standalone catalog bundles pass isolated smoke tests and match their build-receipt hash. Earlier counts and outcomes above are historical, not the final state.

Final inventory is cycling 309 / 32 deep offers / three useful stores; tools 175 / seven / two. First expanded merchant audits passed 30/30 for each. Final repeated audits encountered HTTP 429: cycling 27 matched / three inconclusive; tools 17 / 13. Hosts were stopped after the first block. Snow is 22 matched / eight blocked after an auditor-only retail-price-option correction; original and recheck evidence remain separate. No checkout or market-wide accuracy claim.

Mobile initial price ends at 706.3 px cycling and 738.3 px tools in a 390x844 viewport; no horizontal overflow. Four-action size/package plus budget flows passed. The tools history page visibly reports one observed day and insufficient history. Preview screenshots are in task-owned `.local/catalog-preview/{cycling,tools}-gap-mobile.png`. Temporary browser emulation was cleared.

Publication remains unapproved for this release, and new Vercel project ID secrets/site URL variables are not configured. Existing account secret names were inspected without values. The new workflow refuses publication on merchant audit uncertainty. `benchmark.py ... --require-lead` correctly returns 1: no claim that all ten metrics beat every competitor. See `docs/CATALOG-RELEASE-PLAN.md` and `docs/benchmarks/2026-11-02-gap-closure.md`.
