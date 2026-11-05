# Deal Aggregator workspace refactor

## Competitive gap closure — November 2, 2026

Expanded cycling to three validated sources and tools to two, added independent merchant sampling with blocked checks retained, tightened browsing expiry to 24 hours across all three apps, corrected tool taxonomy and manufacturer aliases, and fixed history continuity across CI runners and deployment bundles. Prepared eight-hour refresh workflows with explicit first-run bootstrap, audit gates, deployment preflight and exact live snapshot verification. 307 offline tests pass. Local mobile price visibility and four-action budget/fit searches pass. Publication and new-site project/domain setup await approval of [the concrete release plan](docs/CATALOG-RELEASE-PLAN.md). Historical completeness and all-competitor leadership are not achieved; see [the gap report](docs/benchmarks/2026-11-02-gap-closure.md). The sections below preserve earlier milestones.

## Cycling and tools implementation — November 2, 2026

The user requested two additional sites and clarified tools means workshop and power tools. Big Ring and Bench Drop are now implemented with their own catalog packages, themes, artwork, sources, classifications and snapshots. Shared snapshot ingestion, query/ranking, responsive browsing, and saved searches live in `common/deal_common/catalog/`; Fresh Powder retains its existing application and deployment entrypoints.

Live local validation found 249 cycling listings above a $1,000 retailer reference across two stores and 71 tools listings above $200 from Woodcraft. Percentage off remains first. 277 offline tests pass. Standalone deployment packaging and a manual artifact workflow are prepared; public deployment, DNS and recurring production refresh remain separate from this build. See [delivery record](docs/tasks/cycling-tools-sites/DELIVERY.md) for exact evidence and limits. Earlier proposal-only statements below describe the prior milestone.

## Purpose

Extract Fresh Powder's methodology and reusable code so additional category catalogs can find exceptionally deep discounts on expensive products.

## Progress

- [x] Inspect source, existing guidance, product history, deployment paths, and tests.
- [x] Preserve pre-existing tooling/research changes and leave ignored operational data in place.
- [x] Move Fresh Powder source, tests, userscript, product documents, and deployment assets into `catalogs/fresh-powder/`.
- [x] Extract category-independent product/retailer models, Shopify/parser utilities, HTTP traversal, and rate limiting into `common/deal_common/`.
- [x] Consolidate installation and update deployment/workflow paths.
- [x] Document the methodology and research a higher-ticket second category.
- [x] Correct default ranking to put discount percentage before image availability.
- [x] Run offline regression tests: 84 passed after extraction, ranking, and deployment-path tests.
- [x] Verify package contents, installed entrypoints, and offline deployment assets.
- [x] Complete final diff and path review.

## Decisions

- 2026-11-02: The user clarified that the core promise is the deepest percentage discounts, especially on originally expensive items. Reviews and fit are supporting features. Running shoes were rejected as the next category.
- Premium cycling is a researched proposal; a narrow inventory experiment should precede a second website. No running-shoe implementation or cycling deployment was created.
- Use one workspace with `common/` and `catalogs/`; retain historical Python import names for Fresh Powder and install all packages from root.
- Keep shared code independent of snow classification and tax policy. Do not generalize the snow database or branded UI without a concrete second catalog implementation.
- Keep the active checkout path, Git remote, cloud projects, and other worktrees unchanged. Root deployment adapters continue selecting Fresh Powder.
- Preserve product plans verbatim under their catalog. Existing untracked research/media and unrelated local edits retain their paths.
- Point new defaults at catalog data paths; leave all pre-existing ignored data untouched. Existing data requires explicit environment overrides.

## Discoveries

- The checked-in workflow runs daily, despite the old README's six-hour claim.
- The previous percentage sort prioritized image presence before percentage; regression coverage now catches that violation.
- System Python lacked app dependencies. The existing project virtual environment runs the baseline and refactored tests.
- The baseline has 79 passing tests. Five new tests cover shared pagination/HTTP failure behavior, discount-first SQL ordering, build assets with a fixture database, and root deployment entrypoint/static serving.

## Validation

Use `.venv/bin/python scripts/check.py -q` for isolated temporary-database tests. Validate wheel contents and offline app/static behavior without reading local production data or triggering downloads, cloud calls, scrape workflows, or deployments.

## Outcomes

Source organization and the shared ingestion boundary are implemented. The second catalog remains research-only. The initial refactor excluded per-variant pricing; the execution milestone below adds it. Live deployment, independent historical reference-price verification, and a generic second-catalog app remain outstanding.

Final verification: 84 tests passed; Python compilation and `git diff --check` passed. Both CLI help commands work after root editable installation. The built wheel contains all three packages plus templates/static assets, excludes databases and tests, and imports/serves static assets in isolation. All 71 relocated tracked files are accounted for; templates, static assets, and the two product plans match their pre-refactor bytes. No live deployment was attempted.

## Strategy execution — 2026-11-02

- Reconciled newer production source from `codex/freshpowder-refresh` (`a0a611b`) with the refactored workspace. The deployed branch already had a 72-hour freshness gate and same-price size summaries; these were not new gaps. Its current comparison pages, source protections, analytics, signup flow, and visual assets are preserved.
- Added shared variant offers, catalog persistence, dated observations, and matching-variant selection before count, ranking, and pagination. Exact-size results require reported stock; sizes between listed lengths are never invented. History is scoped to product name, currency, and variant.
- Added original-price filtering, visible dollar savings and reference basis, model-year labels, stock status, source timestamps, and direct variant links.
- Put category, size, and minimum discount first; reduced the header; verified mobile and desktop layouts. Saved searches persist in this browser without sending email.
- Verification: 234 Python tests and 2 JavaScript tests pass. Targeted lint, package-content verification, and browser size-switch/save/restore checks pass. See the implementation receipt for details.
- Three public retailer feed probes returned HTTP 429. No retries, stock audit, or successful live accuracy measurement followed. A fresh validated snapshot is required before rollout.
- No live deployment, email pilot, second catalog launch, or external outreach was performed. The existing production worktree and ignored operational state were left in place.

## Release preparation and live sample follow-up

- Added a minimum model-year filter without default exclusions, corrected MSRP option display using observed feed evidence, and added per-source variant/confirmed-size coverage to refresh reports.
- Ordinary browser navigation retrieved one public Aspen collection page: 24 raw products, 11 eligible deals, 42 retained variants. Two product spot checks matched merchant price/reference information; these do not satisfy a representative accuracy study or a complete refresh.
- 237 Python tests and 2 JavaScript tests pass in the clean release checkout. Source relocations preserve production files, with the newer production README retained separately in catalog history.
- Prepared `codex/deal-aggregator-release` in a Codex-managed worktree based on current public `main` (`a0a611b`). Original local changes remain in place. Unrelated tooling edits and private research-chat evidence are excluded from the release.
- Publishing the prepared release, running the full refresh, verifying the deployed site, and conducting a consented user pilot remain outstanding. See `docs/RELEASE-PLAN.md` for the exact proposed publication.

## Approved release execution

- The user approved prepared release `4b26de3`, its PR/merge, and the existing full refresh/deploy pipeline.
- PR #2 merged as `758e13c` after successful Vercel checks. The updated production interface is live and category/year/reference filters, pagination, browser-local saved searches, and mobile layout have been checked.
- The prior public snapshot is backed up under the original project's ignored `.local/release-rollback/2026-11-02/` directory. The existing production checkout and operational databases remain unchanged.
- Full refresh run `41525351684` succeeded. The new snapshot is live with 13,171 listings, 25,980 variant offers, and 7,836 products with a reported in-stock size. Production timestamp, exact-size counts/ranking/link consistency, combined filters, pagination, and mobile checks passed. See `docs/RELEASE-RECEIPT.md` for evidence and remaining product-validation limits.


## Competitive benchmark and product improvements — 2026-11-02

- Researched 19 direct, editorial and international capability comparators across snow, cycling and tools. Defined ten fixed metrics, dated evidence and an executable all-metrics lead check. The full lead claim deliberately fails while evidence or coverage is missing.
- Made the two new catalogs compact on mobile, added visible applied filters and offer evidence, and exposed genuine per-variant daily history with explicit insufficient-history wording. Snow cards also show reference/variant evidence.
- Fixed cycling frame/wheel-size conflation, hardened product/variant purchase destinations, protected accessory classification, and retained history across standalone packaging.
- Local mobile first-price distance improved from 1,359 to 783 px for cycling in the paired saved-search state, and 1,351 to 738 px for tools. Current snapshots show 33 / 4 qualifying ≥40%-off cycling/tools listings; tools still has one retailer. See `docs/tasks/competitive-benchmark/verification.md`.
- No publication or recurring benchmark job was activated. Remaining work: independent merchant accuracy samples, broader tools coverage, 30+ real observation days and comparable production performance tests.

## Cycling and tools source expansion — 2026-11-02

- Reused Fresh Powder source discovery and ingestion, with isolated candidate probes, complete pagination, currency/variant or SKU validation, and explicit holds for uncertain candidates.
- Cycling: three to seven retailers, 309 to 956 eligible in-stock listings, 32 to 73 at least 40% off. Tools: two to seven retailers, 175 to 213 eligible listings, seven to nine at least 40% off. Original reference floors retained.
- Added shared Grizzly structured-SKU ingestion and independent product auditing; corrected observed bike taxonomy, shipping-tag and tool accessory/condition errors. Preserved old source timestamps and daily history when merging public preview snapshots.
- Nine newly admitted retailers passed 23 selected merchant checks. Harvey's early rate limits later recovered; Max Warehouse remains held. This is admission evidence, not a representative market-wide accuracy or historical-price claim.
- No push or deployment. See `docs/tasks/source-expansion/IMPLEMENTATION.md` and the dated JSON receipt for sources, retained failures, evidence and remaining tools coverage gaps.
- Final validation: 351 offline tests, scoped Ruff, whitespace checks, both standalone packages and local source-health/page checks passed.

## Continued source expansion to the practical public-feed limit — 2026-11-02

- Expanded cycling from seven to 16 contributing retailers and tools from seven to nine; broadened Tool Nut and Woodcraft without removing prior collections. Final qualifying snapshots: cycling 956 → 1,142 listings and 73 → 87 at least 40% off; tools 213 → 347 and nine → 20. Two additional cycling deep discounts came from refreshing Mike's Bikes, not new retailer coverage.
- Fixed observed apparel/accessory, showroom/blemished and condition-tag errors. Negative shipping tags override positive ones; removed Fanatik pickup-only inventory after separate product-page review. State's manufacturer name no longer makes a tire look like a bicycle. Frame aliases SM/MD/LG now match their full-size equivalents without splitting compound labels.
- Reapplied final cycling rules across all 16 sources, verified 48 distinct sampled merchant offers, and checked local previews plus packaged snapshot hashes. All 377 offline tests, scoped Ruff and whitespace checks passed.
- The researched reusable-feed queue is exhausted for this pass; custom adapters, access recovery and partner feeds remain substantial opportunities. See `docs/tasks/source-expansion/SATURATION.md` and `docs/benchmarks/2026-11-02-source-saturation.json`. No push or public deployment.

## Competitive continuation — 2026-11-03 UTC

- Expanded the evidence registry to 21 competitors, crawled Powder Deals and Velo Bargains to completion, inspected public competitor APIs and measured seven production mobile sites with three cold runs each. Candidate counts remain provisional; the all-metrics lead gate still fails.
- Improved tools recall for jigsaws, oscillating tools and powered ratchets: 351 eligible listings / 21 deep deals across nine sources after a complete refresh. Cycling remains 1,142 / 87 across 16 sources. Both latest 30-offer merchant endpoint samples matched; this does not prove checkout, population accuracy or historical price validity.
- Fixed cycling size facets contaminated by merchant color labels and wheel-only values, refreshed both affected sources, and rebuilt the standalone packages. Snow excludes explicit blemished equipment at ingestion/repair while preserving observation history.
- Production snow LCP was behind Powder Deals and Ski Finder. Earlier stylesheet/font discovery reduced median LCP 792 → 596 ms in a paired local captured-content fixture; production gain remains unverified.
- 405 offline tests, scoped Ruff, whitespace and package/preview snapshot-hash checks passed. Both local catalogs have two actual observed UTC dates, not 30-day history. No push or deployment. Current report: `docs/benchmarks/2026-11-03-competitive-continuation.md`; current publication scope: `docs/CATALOG-RELEASE-PLAN.md`.

## Taylor Toolworks follow-up — 2026-11-03 UTC

- Added a validated exact-SKU HTML/detail adapter using shared request pacing, classification, snapshot replacement and merchant auditing. Complete discovery: 1,917 listing IDs, 186 relevant canonical detail requests, 22 discounted products and one eligible grinder bundle. Accessories remain excluded.
- Tools now has ten contributing retailers, 352 qualifying listings and 22 deep deals from five retailers. The Taylor offer matched a fresh merchant check; the combined top-ten plus seeded-twenty sample matched 30/30. These are endpoint facts, not checkout or historical-price proof.
- Fixed invalid stock quantities passing the Taylor audit. All 440 offline tests and scoped lint pass; package and preview snapshot hashes agree. Local budget-plus-fit tasks show four visible form interactions, with physical gestures and competitor comparisons still unproven.
- Separate follow-up branch leaves pending release 7798318 unchanged. No push or deployment. See `docs/tasks/taylor-source/IMPLEMENTATION.md` and `docs/benchmarks/2026-11-03-taylor-matrix.json`.

## Fasteners Inc follow-up — 2026-11-03 UTC

- Reused the existing Shopify ingestion after observing the current merchant's public backend and validating exact-variant redirects. Five collections completed across 19 JSON pages, with USD verified. Fasteners adds 57 qualifying listings and four deep deals; tools now totals 409 / 26 across 11 contributing retailers, six useful for deep deals.
- Corrected a genuine jigsaw excluded by its blade-stroke specification and classified a trailing-word cordless planer as portable. Package/platform labels remain evidence-bound.
- Fasteners' 30-offer merchant sample and the combined catalog's separate 30-offer sample matched. Seven browser checks matched current-storefront price/reference/stock and retained variants. Samples overlap and do not prove population or checkout accuracy.
- All 445 offline tests, scoped lint and package/preview hash checks passed. Real history and old source timestamps remain intact. The all-metrics lead gate remains unmet. No push or deployment; 7798318's publication scope is unchanged. See `docs/tasks/fasteners-source/IMPLEMENTATION.md`.

## Gravity Coalition follow-up (local only)

Prepared a seventeenth cycling source after two complete currency-verified collection refreshes: 29 eligible listings, six deep discounts, and 29/29 merchant endpoint matches. Fixed manufacturer-name and frame-only classification defects with six regression cases; 451 offline tests pass. This follows unpublished Taylor/Fasteners work, is outside release 7798318, and remains unpushed. See `docs/tasks/gravity-source/IMPLEMENTATION.md`.
## Approved catalog release: CI parity fix (2026-11-03 UTC)

- User approved publishing release `7798318`, merging after checks, and the three-catalog rollout in `docs/CATALOG-RELEASE-PLAN.md`. PR #4 initially failed lint because CI installed Ruff 0.17.3 while local validation used 0.15.11.
- Pinned Ruff 0.17.3 and applied its import, UTC-alias, literal-dictionary and equivalent-condition fixes. Preserved restore's invalid-response ValueError contract. Later Taylor/Fasteners additions remain outside this release.
- Validation: all 405 offline tests pass; the exact CI lint command passes on Ruff 0.17.3; JavaScript syntax and whitespace checks pass.

## Catalog production source recovery

PR #4 merged after CI passed. First production tools refresh exposed Grizzly HTTP 403; eight other feeds completed. Quarantine the inaccessible feed and show the coverage limitation on the source page; preserve all completeness and merchant-audit gates. Cycling and snow refreshes continue independently.

## Catalog audit retry recovery

Run `41576984053` produced 30/30 matching tools audit samples and a valid eight-source package (327 eligible listings), then deployment failed because the existing GitHub Vercel token is invalid. Token creation through the authenticated CLI app is forbidden; requested user renewal of the existing repository secret and continuing deployment through normal local CLI authentication. Cycling matched 27/30 with three inconclusive after Colorado Cyclist HTTP 429; Pro Bike Supply passed this time. Reuse the shared bounded HTTP retry helper so audits honor Retry-After (up to 60 seconds) without changing endpoints or networks. HTTP 403 still stops immediately; exhausted retries remain inconclusive and block publication.

## Source follow-up integration — 2026-11-03 UTC

Merged production recovery through `0530cad` into the unpublished Taylor/Fasteners/Gravity branch. Kept Grizzly excluded, preserved the new feeds, and applied the shared bounded audit retries to Taylor. Resolved import/documentation conflicts without losing either task history. All 454 offline tests, Ruff 0.17.3 CI checks plus changed HTTP/parser tests, JavaScript syntax and whitespace checks pass. This is local integration, not approval or evidence of production admission for the three additional feeds.

## Approved rollout verified — 2026-11-03 UTC

Repaired the Gmail OAuth rejection, completed the scoped verification-code lookup and updated the GitHub Vercel secret. Catalog run `41580573050` passed both 30/30 merchant audits, deployment and exact production hash checks. Live smoke checks passed at 05:00 UTC. Snow run `41576089057` also succeeded. Current counts, hashes, source limitations and unpublished follow-up scope are recorded in `docs/CATALOG-RELEASE-RECEIPT.md`; all-metric competitive leadership remains unproven.

## Source and quality admission — 2026-11-03 UTC

Fresh combined refreshes completed for 17 cycling and ten tools sources; both merchant audits matched 30/30. Local eligible/deep/useful-retailer counts are cycling 1,170/93/12 and tools 607/24/5. Ski Essentials now completes all six collections after a narrowly scoped newsletter dismissal (1,853 unique products, 899 discounts). Model/category regressions, bike accessory taxonomy, invalid frame dimensions and non-manufacturer vendor labels were corrected. Targeted rechecks preserved the eligible audited offer maps. Desktop/mobile inspection caught and fixed clipped square images. Benchmark comparisons now reject local layout and out-of-window speed evidence. All 489 tests and scoped checks pass. See `docs/SOURCE-QUALITY-RELEASE-PLAN.md` for the concrete unpublished release and retained admission evidence.


## Variant shipping evidence — 2026-11-03 UTC

On separate branch `codex/variant-shipping-evidence`, preserve Harvey ESD notices on their exact color variants and withhold confirmed-stock status. The independent product audit rejects the delayed black G-700Pro while white passes; UI cards and dated history retain the notice. A fresh Harvey-only refresh in a copied public snapshot changes one of 14 offers to unknown, preserving 607 eligible tools listings and all unrelated source records. 501 offline tests and scoped Ruff checks pass; desktop and mobile history layouts were inspected. See `docs/SHIPPING-EVIDENCE-FOLLOWUP.md` and its public receipt. This is local follow-up work, separate from the pending publication request for `35f2bfb`.


## Preserve history across manufacturer-label cleanup — 2026-11-03 UTC

Shared the existing fulfillment-label normalization between ingestion and history identity comparison. A prior In Stock / Out of Stock / ESD label now matches the current Unspecified manufacturer only when the source, product URL/name, variant ID/options and destination still match. Historical records remain unchanged. Nine regressions cover preservation of dates/prices/references/stock, read-only behavior, and rejection of real manufacturer, model, package or variant changes. All 510 offline tests and catalog Ruff checks pass. The inspected Harvey public snapshot contains one real observation day; this correction does not create or claim recovered history there. Follow-up remains local, separate from publication approval for `35f2bfb`.


## Rockler public category feed discovered — 2026-11-03 UTC

Observed the storefront's real category API and traversed all ten sale pages: 223 unique listings, 62 preliminary equipment discounts above the reference floor and seven nominal deep discounts. This supersedes the earlier empty text-search probe, which contained a merchandising redirect. Admission remains held: 227 advertised versus 223 returned records is unresolved, and sampled Axiom SKU 77007's structured InStock conflicts with a future manufacturer shipping date. Recorded public evidence and implementation gates in `docs/tasks/rockler-source/RESEARCH.md`. No retailer configuration, catalog snapshot or deployment changed.

## Rockler decoder and delivery evidence — 2026-11-03 UTC

Resolved the four-count discrepancy as inline banner slots: the banner-free traversal returns the same 223 unique products across ten complete pages. Located the public delivery endpoint; all seven nominal deep candidates have future manufacturer shipment estimates, while a sampled Bosch jigsaw is explicitly ready to ship. Added exact simple-SKU decoding, active shipping notices, opt-in bounded delivery requests and independent-fetch audit support. Full-price promotions skip stock requests; off-host evidence and redirects are rejected. The candidate refresh exhausted bounded retries on HTTP 429 after five product pages, so Rockler remains disabled with zero admitted inventory. No repeated live retry or production change followed. All 531 offline tests and scoped Ruff checks pass. Research and the dated admission receipt preserve the limitation. Work remains local on `codex/rockler-source`; the pending `35f2bfb` publication scope is unchanged.

## Standing release authorization and approved rollout — 2026-11-03 UTC

The user approved release `35f2bfb` and comparable future releases for these three sites without another publication confirmation. Continue tests, merchant audits and exact deployed-snapshot verification; this does not authorize unrelated account, spending or product changes. PR #7 passed CI and Vercel preview checks and merged as `9b421b7`. Fresh catalog run `41678692421` and full snow run `41678695345` are running with preserved history and no bootstrap. Their terminal deployment results still require verification.

## Bike Closet source admission — 2026-11-03 UTC

Added a public WooCommerce decoder with header/count reconciliation and exact parent/variant destinations. The completed candidate yields 19 in-stock deep listings after excluding a merchant SIZE L / variant XS conflict; six delayed variants remain unknown. All 19 separate merchant checks match, but their elapsed time exceeds the strict M3 measurement window. No accuracy-lead claim follows. TIME category labels, regional shipping restrictions, final-sale terms and frameset-photo caveats are preserved. 546 offline tests and scoped Ruff pass; mobile source preview has zero initial scroll to price and no horizontal overflow. See `docs/tasks/bike-closet-source/IMPLEMENTATION.md`. This follow-up is local and requires fresh runner-side checks before publishing under the new standing authorization.

## Bound merchant audit observations — 2026-11-03 UTC

On separate branch `codex/audit-window`, enforce a 15-minute observation window in the shared merchant auditor. Record completion time, keep late factual checks as inconclusive, stop subsequent endpoints after expiry, and latch invalid backwards-clock observations. Four controlled-clock regressions cover the boundary and request stopping; all 550 offline tests pass. Prior evidence is unchanged and the gate alone does not establish comparative M3 accuracy. PR #8 remains frozen at `cb8672e` with passing checks while PR #7's live refreshes finish. Publish this correction as a separately reviewed follow-up under standing authorization.

## evo cycling admission — 2026-11-03 UTC

Revisited the earlier zero-admission result and found that exact complete-bike retailer taxonomy was missing from classification. The complete 493-product feed now yields 55 eligible listings and three deep deals, excluding 14 store-only products and one blemished product. A fresh currency-verified refresh and 30/30 separate merchant sample passed within 163 seconds. Browser checks confirmed all three deep variants plus a contradictory shipping-tag exclusion; checkout shipping fees remain excluded from prices. Nine regressions bring the suite to 559 passing tests. See `docs/tasks/evo-cycling/IMPLEMENTATION.md`. The new nineteenth local source follows the frozen Bike Closet and audit-window releases.

## Discount precision and rollout verification — November 4, 2026 UTC

Shared discount calculations now preserve price precision for eligibility, variant selection and ordering. Snow derives percentages from prices even for read-only older snapshots. Fourteen regressions cover threshold boundaries, rounded ties and old-snapshot counts/pagination. All 573 offline tests and CI lint pass. See [implementation and correction receipt](docs/tasks/discount-precision/IMPLEMENTATION.md). Publication remains queued behind the tested source/audit releases under standing authorization.

The PR #7 catalog and snow workflows succeeded; [rollout evidence](docs/benchmarks/2026-11-04-source-quality-rollout.json) records actual totals, retained source limitations, subsequent snow refreshes and the local TLS failure that prevented additional snow page checks. No all-competitor leadership claim is made.

## Verified cycling/tools follow-up — November 4, 2026 UTC

PR #8 merged as `6f52cfb`; catalog workflow `41770144751` completed successfully. Independent live hashes, selected variant links, stock/budget filters, shipping notices and history were checked. Big Ring has 1,205 in-stock listings / 113 deep deals / 13 useful retailers; Bench Drop has 583 / 24 / five. The full snow workflow `41770152754` remains active. See the [receipt and remaining limits](docs/benchmarks/2026-11-04-follow-up.md). The expanded 22-competitor matrix supports four strict leads out of 260 comparisons; all-metric leadership remains unproven.

- November 4, 04:27 UTC continuation: snow run 41770152754 passed production HTTPS/timestamp verification; 13,586 raw listings, The House recovered, MEC 403. Merged green PRs #9/#10/#11 as 0bd7216, 75cce88 and 89f5d2e. Four-action cycling XS/budget task passed; controlled loading remains unmeasured. Fresh cycling/tools rollout is still required for the merged precision/evo release. Evidence PR #12 retains these limitations.

- Snow variant disclosure follow-up: production inspection found the selected variant key was dropped between SQL and AggregatedDeal, creating a false unknown-variant notice. Added the optional field and mapping; three strengthened regression checks failed before and pass after. Full 573-test suite and exact CI lint pass. Catalog refresh 41773486321 runs independently at merged release 7ebabce with history restoration.

- Catalog restore follow-up: cycling job 126388372512 failed on anonymous GitHub metadata HTTP 403 rate limiting before refreshing; its live snapshot remains unchanged. Scope existing read-only workflow token to the fixed metadata endpoint only, keep downloads unauthenticated, and reject metadata redirects. Four added regression cases bring the full suite to 577 passing tests; exact CI lint passes. Snow disclosure PR #13 merged as 9692be9 after manual branch CI 41773615030 passed.

- November 4 reference evidence pass: first-page M6 now measured at cycling 24/24, tools 24/24, snow 35/60. Twelve of snow's 25 missing variant identities are Ski Essentials. Discovered and verified its normal public pagination feed and SKU-specific online-price mapping; full six-collection probe 91868 is running before adapter implementation/admission. Additional Great Lakes Power Tools, Toolmarts and Toolup requests returned HTTP403 and were not retried or enabled. Tools job in run41773486321 passed30/30 and exact live hash cac9476d; corrected run41774045047 restored both histories and is collecting sources.

- Ski Essentials exact-offer adapter: complete 1,857-listing traversal and 48-response candidate ingestion produced 482 eligible products / 1,251 variants. Independent 30/30 product-page checks bind price, reference, currency, stock, options and selected destination. Reconciliation removes 424 unconfigured bundles and six unsupported offers while adding six; history/canonical identity stays unchanged. 605 offline tests and exact CI lint pass. Release under standing approval; targeted production refresh and exact-size verification follow merge.
- Corrected catalog run41774045047 completed both deployments: Big Ring19/19 fresh sources, 1,277 eligible /115 deep deals /14 useful retailers; Bench Drop10/10 sources. Both 30/30 merchant audits and exact production hashes verified, with November3 and4 dated history preserved. Cycling evo≥40 returns two precise matches; XS/budget1500/≥40 returns12 matching cards.

- Ski Essentials rollout verified: PR #15 merged as `ad80035`; targeted workflow `41776930375` completed successfully. The live snapshot has 482 eligible source products and 1,250 exact offers. Full/partial routes select the available 178 cm XO H21 at $199 and exclude sold-out 172 cm; seven 178 cm / ≥40% / ≤$700 results have matching stock, options, destinations and precise ordering. Fresh postpublication merchant sample passed 30/30 within 15 minutes. Every previous price-history and offer-observation row remains intact. First-page snow M6 rose from 35/60 to 46/60; the remaining 14 cards and local-only custom-host TLS failure are explicitly recorded. Strict competitor leads remain four out of 260.

## Beaver and RA source expansion — November 4, 2026 UTC

Beaver completed three feed pages and 192 exact purchase checks: 75 confirmed-stock listings above the $200 reference floor, including seven deep deals. Independent admission passed 30/30. Delayed stock retains its notice and cannot pass confirmed-stock filters. A local preview preserves all 20 baseline observation rows and percentage-first ordering.

RA's completed three-page candidate yields 116 confirmed-stock listings above $1,000 reference, including 64 deep deals. Exact inventory, numeric-s frame sizes and final-sale notices are bound to the selected variant. Two local merchant audits expired during execution pauses, with zero mismatches but inconclusive results; RA remains unconfigured. The existing check workflow gains an opt-in isolated runner admission, preserving the 15-minute audit rule and all original failed evidence. Bolton remains disabled because the active warehouse restriction lacks product-level freight eligibility. No competitive-lead claim follows from these candidate counts.

- PR17 preview exposed a snow deployment blocker: the latest public snapshot made the function exceed Vercel’s 225 MB limit. A temporary-copy compaction check saved 9,773,056 bytes with identical schema and complete table contents, including 164,108 price-history and 203,174 offer-observation rows. Build-time compaction preserves timestamps/history and leaves the skip-download path untouched; provider verification is pending. The earlier scheduled snow run41833976108 failed production-snapshot verification and is not treated as a successful deployment.

- RA runner admission `41874414409` passed 76/76 after complete three-page/144-product traversal; enabled its verified cohort locally. Combined preview adds 116 confirmed-stock / 64 deep cycling listings and 75 / seven tools listings while preserving all 36 + 20 baseline history rows. Final snow build optimization preserves all historical rows and removes only a proven redundant index, reducing the public build copy to 125,919,232 bytes; provider preview Ready. 744 offline tests pass; production rollout pending.

- PR17 merged as `1eec6c9`; workflow `41882144887` successfully refreshed, audited and deployed both catalogs. Exact live hashes verify Big Ring 20/20 fresh sources, 1,347 qualifying in-stock listings / 166 deep deals / 15 useful retailers, and Bench Drop 11/11 sources, 454 / 31 / six. Both 30-offer merchant samples passed. RA adds 116 / 64; Beaver adds 69 / seven. All prior-day observation rows remain identical; same-day observations legitimately update. Exact 50s/50cm, purchase links, notices and delayed-stock exclusion pass. Snow production build recovery and full/partial exact-size checks pass on the provider URL; local custom-host TLS remains unresolved. See `docs/benchmarks/2026-11-04-pr17-rollout.json`. The updated matrix still supports four strict leads / 260 comparisons; the overall goal remains open.

- Big Ring M9 now has three production 390×844 geometry observations: first full price at 706.3 px, zero initial scroll, no horizontal overflow or saved searches. A separate four-action XS/$1,500 form check returns 24 matching visible cards and brings the first price into view; three failed automation selectors are disclosed. This replaces its local geometry evidence without claiming LCP performance or a matched competitor task. Original competitor dates remain unchanged; strict leads remain four / 260. See `docs/benchmarks/2026-11-04-pr17-mobile.json`.

## Snow completeness correction — November 5, 2026 UTC

Scheduled snow run `41948669174` completed deployment but reported incomplete Backcountry pagination. The existing admission guard only withheld count collapses, so partial results could renew observations. A focused fix now withholds explicit errors and non-complete collections before persistence, including new sources and healthy-count partial results. Temporary-database CLI tests verify retained prices, offers, timestamps and history plus the accepted-source minimum. See [release plan](docs/SNOW-COMPLETENESS-RELEASE-PLAN.md); independent review and all 750 offline tests passed. PR #19 merged; targeted workflow `41966876680` refreshed and deployed successfully, preserving all unselected source rows and prior observations. The [verified receipt](docs/benchmarks/2026-11-05-snow-completeness-rollout.json) separates live success-path checks from failed-source regression evidence.

## Snow cash-savings ties — November 5, 2026 UTC

Default snow ranking now keeps exact percentage first and uses cash savings to break same-currency ties in ingestion, selected offers and cards. Mixed-currency ties group USD first, then actual currency code, without nominal-money comparison or conversion. Four regressions cover eligibility, metadata, pagination, near-percentage differences and explicit alternative sorts; independent isolated release validation passes 754 tests. The House candidate remains separate. PR #21 merged as `895fd0b` after passing CI. Production verification passed eight full/partial route/filter combinations and 480 rendered card observations against the exact public snapshot. See [rollout receipt](docs/benchmarks/2026-11-05-snow-ranking-rollout.json). No freshness or competitor-lead claim changes.


## Tools equipment recall — November 5, 2026 UTC

Live source research exposed complete tools and fixed packages excluded merely because their titles mention included blades or filters. The tools-owned correction distinguishes the primary item, preserves accessory/condition gates and exposes explicit bundles. Separate research checks match 63 newly identified products' identities and money: 51 explicitly in stock and 12 with a 5–7-day shipping notice that must remain unknown stock. Full-feed and existing-snapshot replay also exposed router/package-label regressions for independent review and a previously misclassified saw-blade pack. No new retailer or deep-deal increase is claimed from research. See [scope and release gates](docs/TOOLS-EQUIPMENT-RECALL-RELEASE-PLAN.md); independent review passes 797 tests, all eleven candidate sources complete, and 95/95 merchant checks match. The correction recovers 69 eligible in-stock listings on the same candidate population, including two at least 40% off. Production verification is recorded below.

## Snow compressed snapshot repair — November 5, 2026 UTC

The scheduled snow deployment and tools PR preview fail the enforced function-size cap despite prior lossless DB compaction. A separate packaging repair will compress the exact validated snapshot, reconstruct a verified read-only local copy before DB defaults load, and preserve all history. Current public data has 190,839 price-history rows and 250,212 offer observations; existing preparation preserves their complete row digests. See docs/SNOW-COMPRESSED-SNAPSHOT-RELEASE-PLAN.md. Tools PR23 remains preserved pending the repaired deployment gate.

- PR #24 merged as `2d975f0` after 776 tests, green CI and successful Git/runner previews. Production `dpl_9PfzK8oeLLWXMHbR2SPvv2WucdJL` is Ready, packaging 147,640,320 prepared bytes as 18,279,304 compressed bytes. The custom hostname passes HTTPS and serves the 13:40 snapshot; eight route/filter combinations and 480 selected-card observations match. The combined tools branch passes 819 tests. See [rollout receipt](docs/benchmarks/2026-11-05-snow-compressed-rollout.json).

## Tools recall production verification — November 5, 2026 UTC

PR #23 merged as `64d8ed6` after 819 offline tests and green CI. Audited workflow `42089645493` completed both production deployments. Bench Drop serves 514 qualifying in-stock listings, including 32 at least 40% off from 6 useful retailers; all eleven sources are fresh. Big Ring serves 1,375 / 180 from 16 useful retailers, with all twenty sources fresh. Both current 30-offer merchant audits passed.

Live snapshot hashes match the deployment artifacts. 8 tools routes and 6 cycling routes match the exact packaged data, covering 265 card observations and 10 history pages. All 21 tools and 37 cycling prior-day observation rows remain exact; latest same-day rows are replaced under the existing daily policy. Bundle and delayed-stock filters, cycling XS/budget and exact 50s variants pass.

The final retained tools population yields 445 in-stock listings under the old classifier and 514 under the correction: 69 recovered listings, including 2 deep deals. All recovered offers retain the identity, price, reference, options and stock fields checked in the earlier 95-offer audit; that evidence remains dated. The new production audit is a separate 30-offer sample. Cycling inventory changes are not attributed to the tools correction.

The [rollout receipt](docs/benchmarks/2026-11-05-tools-recall-rollout.json) and [updated matrix](docs/benchmarks/2026-11-05-tools-recall-matrix.md) retain evidence dates and limitations. Rockler remains inactive after a complete 215-product feed traversal exposed a contradictory canonical destination on the first deep product detail; see the [bounded recheck](docs/benchmarks/2026-11-05-rockler-recheck.json). No request or stock gate was weakened.

## Shared size-menu cleanup — November 5, 2026 UTC

Big Ring repeats equivalent size labels despite already matching them identically. The shared catalog query now exposes one stable original label per existing size_key group; legacy URLs show the matching representative selected. Exact merchant variants, prices, links, counts and history remain unchanged. Read-only public-snapshot replay reduces cycling's 164 labels to 128 across 166 filter cases and 497 pages; tools remains at four labels across six cases and 27 pages. All selected cards/order/counts/pagination match the baseline, and input DB hashes remain unchanged. See docs/tasks/size-facet-labels/. Independent review passes 828 tests. PR #26 merged and both catalog deployments are verified Ready. Ten live route checks and a mobile legacy-link check pass; all source timestamps and all 89 source-history rows are unchanged. See [rollout receipt](docs/benchmarks/2026-11-05-size-facet-rollout.json). Mobile paint instrumentation is unavailable through the selected native browser; no new comparative speed claim is made.
