# Three-catalog quality release

Branch: `codex/cycling-tools-sites`, repository `lifan-builds/snow-deal`. This is a new release; the earlier approval for `4b26de3` covered the completed snow rollout only.

## Reviewable result

- Big Ring and Bench Drop are standalone server-rendered sites using the shared catalog runtime. Snow retains its existing application and root Vercel project.
- All three expire browsing offers after 24 hours. Failed checks do not renew data; snow health now reports the latest successful check separately from the latest attempt.
- Cycling has 16 enabled retailers and tools nine after the [source expansion](tasks/source-expansion/SATURATION.md). USD, complete pagination and exact variant/SKU checks remain mandatory. Grizzly uses public structured SKU data; other enabled new sources use Shopify. Observed shipping/condition/accessory exclusions are covered by regression tests.
- Compact mobile pages, budget/fit/package filters, removable filter chips, reference evidence and actual per-variant daily history are included. Percentage off stays first; savings break ties.
- History survives refresh runners and deployment packaging. Storage keeps the latest successful observation per UTC day within 45 days; no fabricated backfill.
- New-catalog releases require a complete refresh, a top-ten plus twenty seeded merchant audit, a nonempty fresh package and an exact public snapshot hash match. HTTP success with an old snapshot fails verification. Unknown merchant checks block publication.

Current local packages are `.local/catalog-preview/bigring-competitive-final/` and `.local/catalog-preview/benchdrop-competitive-final/`, each with `BUILD-RECEIPT.json`. Both packages and running previews passed exact snapshot-hash checks. Older packages predate the latest corrections. These contain explicit public inventory only and are not proof of deployment. Rebuild from fresh, audited snapshots during publication; old local receipts are not permission to publish stale data.

Latest local inventory: cycling 1,142 eligible in-stock listings / 87 at least 40% off / 16 contributing retailers; tools 351 / 21 / nine. Eleven cycling retailers and four tools retailers contribute at least one deep deal. Thresholds remain $1,000 and $200 retailer references. See [the dated competitive report](benchmarks/2026-11-03-competitive-continuation.md) and its evidence receipts.

Merchant evidence and limitations are retained in `docs/benchmarks/2026-11-02-*-audit.json`. Cycling's earlier audit matched 30/30; the final repeat matched 27 and left three inconclusive after Bicycle Warehouse HTTP 429. Tools' expanded-source audit matched 30/30; a later repeat encountered Tool Nut HTTP 429 and stopped that host, leaving 17 matches and 13 inconclusive. Snow has 22 matches and eight blocked checks after correcting an auditor-only metadata mismatch. None proves 99% population accuracy, checkout availability or historical selling prices. The later failed audit is not discarded.

The November 3 UTC follow-up adds jigsaw/oscillating-tool/powered-ratchet recognition, withholds mislabeled cycling colors and wheel diameters from frame-size filters, excludes explicit blemished snow equipment, and discovers snow styles/fonts earlier. Full raw variant descriptions and purchase identities remain intact.

The latest cycling and tools audits both matched 30/30, with seed 20261103 and zero inconclusive checks. Receipts are `docs/benchmarks/2026-11-03-cycling-merchant-audit.json` and `2026-11-03-tools-merchant-audit.json`. This is newer evidence, not erasure of earlier failures. All 405 offline tests, scoped Ruff and whitespace checks pass. Production Fresh Powder LCP is behind Powder Deals and Ski Finder; the prepared fix improves a controlled local fixture by 25%, and requires production remeasurement.

## Publication actions requiring the user's release approval

1. Review and commit the scoped work, push the release branch, open a PR, inspect required CI and merge only after it passes. A root merge can deploy the snow application through its existing Vercel integration.
2. Create two separate Vercel projects, `bigring` and `benchdrop`, using the existing account. Configure their production domains as `bigring.clifan.com` and `benchdrop.clifan.com`; do not replace the snow project or repoint its domain. Use the existing plan; stop if a paid upgrade or conflicting domain ownership is required. The catalog projects deploy from the generated standalone bundles, not the root snow entrypoint. Do not attach an independent root Git auto-deploy that would publish the wrong app.
3. Configure repository secrets `CYCLING_VERCEL_PROJECT_ID` and `TOOLS_VERCEL_PROJECT_ID`, and variables `CYCLING_SITE_URL` and `TOOLS_SITE_URL`. Existing names `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `DATA_REPO_TOKEN` were confirmed present without reading values; the new IDs and site variables were absent. Use the normal authenticated provider tooling, never copy credentials into source or receipts.
4. Run the new `catalog-refresh.yml` once with explicit `bootstrap_history=true` for the missing first release assets. A missing history asset is thereafter a hard failure; never enable bootstrap to recover from corruption or download failure. Inconclusive or mismatched merchant audits must be resolved before that catalog can publish. Do not bypass HTTP 403/429 or the audit gate.
5. Publish validated `cycling.db` and `tools.db` alongside the existing public data release, deploy each generated bundle via pinned Vercel CLI, and verify the expected fingerprint at its public domain. Run the existing full snow refresh/deploy pipeline and its timestamp checks.
6. Merging activates three scheduled checks per day: snow at 05:17, 13:17 and 21:17 UTC; cycling/tools at 00:43, 08:43 and 16:43 UTC. Schedules can be delayed by CI. New-catalog runs restore history, refresh, audit, package, retain data, deploy and verify; failure is visible and does not become a successful release. Artifacts retain audit failures for 30 days. No email alerts, outreach or separate Codex automation is activated.
7. Confirm live filtering, purchase destinations, mobile layout and history. Measure production LCP/CLS in three comparable cold runs. Record a release receipt; do not mark deployment complete from a hook, upload or green build alone.

## Recovery and remaining evidence

If publication fails, leave the last verified public deployment in place. If an incorrect deployment was promoted, restore the previous verified app/data deployment together. Preserve public snapshot history and failure receipts. Disable only the new failing workflow schedule if necessary; do not reset unrelated working trees or delete history.

The market-leading claim remains unproven. Required follow-up includes more qualifying deep-discount retailers, representative same-cohort competitor merchant audits, exact-fit tasks, production measurements of released changes, and at least 30 genuinely observed UTC dates. An eight-hour schedule or 405 passing tests does not fill these gaps. At 100% accuracy or zero scroll, strict superiority may be impossible; report parity honestly. See the dated gap scorecard and `COMPETITIVE-BENCHMARK.md`.

## Approved rollout update — November 3, 2026 UTC

The user approved release `7798318`. PR #4 merged as `0b3bf0e` after all checks passed, including the Ruff 0.17.3 parity fix `2103ed5` and 405 offline tests. Both Vercel projects and DNS routes are configured on the existing account.

Initial tools refresh job `125719815260` in run `41576092687` received HTTP 403 from Grizzly Industrial before reading any listing pages; the other eight retailers completed. No tools snapshot or deployment was published. Grizzly is quarantined from the enabled catalog, and the public source page explicitly explains the missing coverage. No alternate IP, endpoint or session is used to bypass its refusal. The release now targets eight active tools retailers; earlier nine-retailer inventory totals remain historical local evidence. All active-source completeness, merchant audit and exact deployment fingerprint gates remain mandatory. Re-admission requires a fresh successful production-runner probe and audit.

Cycling's first production audit matched 24/30 offers, with zero mismatches and six inconclusive checks after Pro Bike Supply returned HTTP 429. The audit stopped further requests to that host. The next run increases spacing between audit requests from 1.5 to 5 seconds; it must still produce 30 matches before publication. Preserve this failed audit as evidence. Future workflow artifacts also retain the public source-refresh report on failed refreshes.
