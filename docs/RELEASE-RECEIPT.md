# Fresh Powder rollout receipt — November 2, 2026

Status: approved application and data rollout complete. Production and the refreshed offer path are verified.

## Publication

- Approved prepared revision: `4b26de3`, including the workspace extraction and executable startup script.
- [PR #2](https://github.com/lifan-builds/snow-deal/pull/2): merged after successful Vercel preview checks.
- Merge revision: `758e13c94f9b14ffdecd637e1d417221c9b999aa`, November 2 at 21:06:46 UTC.
- [Full refresh](https://github.com/lifan-builds/snow-deal/actions/runs/41525351684): dispatched against that merge with review refresh disabled. Parser/data-contract tests, scrape quality gates, snapshot publication, deploy hook, and production timestamp verification passed. The workflow completed successfully at 21:37 UTC.
- Production: [freshpowder.clifan.com](https://freshpowder.clifan.com/).

## Recovery preparation

The prior public snapshot was downloaded before replacement. Release asset `702002844` was 28,553,216 bytes, updated at 14:19:48 UTC, with SHA-256 `9a94322337aa4441667c6f42f45f6315e0b902fa80be87429193284bdfbc8b62`. The local ignored rollback copy and metadata are under the original project's `.local/release-rollback/2026-11-02/`. Its paired application revision is `a0a611b`. Existing operational databases and original uncommitted work were preserved.

The preceding refresh report is retained alongside the backup: 31 configured sources, 30 with deals, 13,531 published listings, no withheld stores, and report timestamp `2026-11-02T14:19:31.248277`. MEC returned no deals. These are ingestion counts across all categories, not the equipment-only homepage count.

## Checks completed

- Before publication: 237 Python tests, 2 JavaScript tests, targeted lint/syntax checks, wheel inventory, relocated-file review, and synthetic size/year/pagination/saved-search flows.
- Live interface: updated header, offer cards, reference-price labels, model years, stock uncertainty, and source timestamps are present.
- Live category/year filtering: skis with model year 2025 or later returned 1,790 results on the preceding snapshot. Pagination added the next 60 cards while preserving filters.
- Live saved search: persisted across reload, restored its category/year URL, and the temporary verification entry was removed.
- Mobile at 390 × 844: the main filters and first offer are visible without horizontal clipping. Combined USD, skis, model year 2025+, and retailer-reference floor $1,000 returned 446 results on the preceding snapshot, retaining percentage-first order.

Those counts describe the earlier snapshot, not the final refresh. Schema migration alone does not establish variant coverage.

## Completed refreshed-data checks

[Quality report](research/2026-11-02-deal-site-landscape/execution/release-quality/scrape-report.json): 13,171 listings from 30 of 31 configured sources, 25,980 variant offers across 8,065 products, and 7,836 products with a size reported in stock. Fetched and publish-candidate coverage agree; no sources were withheld. MEC returned no deals. The listing count is 360 lower than the previous refresh; the existing completeness gates passed. These are coverage metrics, not a merchant-accuracy rate. Sources without variant evidence remain browsable with stock uncertainty and do not satisfy exact-size requests.

Production `/healthz` returned `status: ok`, 30 stores, and `checked_at: 2026-11-02T21:35:36.450747`, matching the report. Published data asset `703257183` is 55,119,872 bytes; SHA-256 `eccd99def882c9c2f116bcb068b1bc9f3f1dbe4eebf4cb1bb99ce41f6a66864f`. The downloaded release copy passed SQLite integrity checking and contains 25,980 current offers and 25,980 dated observations. It was opened read-only for these authorized release checks.

[Snapshot checks](research/2026-11-02-deal-site-landscape/execution/release-quality/snapshot-checks.json) verified result/count equality, descending discount order, exact normalized size, reported stock, and matching price/reference/purchase URL against persisted offers for all results in four searches: 180 cm skis (91), 180 cm skis with USD reference $1,000+ and model year 2025+ (21), size 24.5 ski boots (449), and 156 cm snowboards (95). These prove internal consistency, not independent retailer accuracy.

Live browser results matched the 91, 21, and 449 counts. Loading the remaining 180 cm ski results produced exactly 91 cards and removed the pagination link. The leading ski offer selected Ski Pro's Atomic Bent 110, variant `46081304133809`, MULTI / 180, at $449.95 versus $900. The merchant's product lookup reported that exact variant available, and its Add to cart control was enabled. Generic radio accessibility labels also contained sold-out wording; the structured variant response is preserved with that limitation in the [merchant observation](research/2026-11-02-deal-site-landscape/execution/release-quality/merchant-check.json). No cart or checkout action occurred.

Final production screenshots: [desktop](research/2026-11-02-deal-site-landscape/execution/release-quality/live-desktop.png) and [390 × 844 mobile](research/2026-11-02-deal-site-landscape/execution/release-quality/live-mobile.png). Mobile document width and scroll width both measured 390 px, and the first selected offer's price is visible. Temporary browser emulation was cleared.

## Product validation beyond this release

The bounded Aspen feed and two merchant observations do not establish the proposed 95-of-100 accuracy target. A representative multi-day merchant audit and consented shopper pilot remain necessary before claiming a competitive reliability or retention advantage. Reference prices are retailer claims, not independently verified historical selling prices. Cycling stays research-only; no outreach or email pilot was sent.
