# Deal Aggregator workspace refactor

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
