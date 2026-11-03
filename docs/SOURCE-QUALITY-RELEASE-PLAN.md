# Source coverage and quality release — prepared 3 November 2026 UTC

Repository: `lifan-builds/snow-deal`. Branch: `codex/gravity-source`. Production baseline: `0530cad`. Publication of this follow-up remains pending approval; the previous approval covered release `7798318` and its rollout recovery.

## Result to publish

- Big Ring gains Gravity Coalition. A complete refreshed catalog has 1,170 eligible in-stock listings and 93 qualifying deep deals from 12 useful retailers, versus verified production's 1,141 / 87 / 11. All 17 configured sources completed.
- Bench Drop gains Taylor Toolworks and Fasteners Inc. Its fresh catalog has 607 eligible listings and 24 qualifying deep deals from five useful retailers, versus verified production's 548 / 19 / three. All ten configured sources completed, including 186 bounded Taylor detail-page checks.
- Fresh Powder's Ski Essentials traversal dismisses the observed newsletter popup before Show More. All six collections completed locally: 1,853 unique products and 899 discounted listings. Three verified model-only names now classify as equipment; Sidas Cambrelle Covers classify as accessories. Size and stock remain unknown when the listing does not supply them.
- Source classification rejects the observed bike locks, pumps, computers, lights and parts, plus kitchen grinders. Cable lengths and tire dimensions cannot become frame-size filters. Fulfillment messages in a vendor field are labeled as an unspecified manufacturer; they do not establish stock.
- Shared product photos fit inside their cards instead of clipping square images. The stylesheet URL is versioned so returning browsers receive the correction.
- The benchmark requires production layout evidence and documented speed runs within one hour. Current evidence supports four strict leads among 250 comparisons, not leadership on all metrics.

Deep deals mean at least 40% off a retailer reference of at least $1,000 for cycling or $200 for tools. Counts are listings, not cross-retailer unique models. Inventory changes between observations can affect totals.

## Validation and evidence

- 489 offline tests pass. Exact CI Ruff checks, changed benchmark/pagination checks, JavaScript syntax and whitespace checks pass.
- Both fresh catalog merchant audits matched 30/30 sampled offers with no inconclusive results. Subsequent targeted classification refreshes preserved every eligible selected offer and its price/reference/options/stock; original audit timestamps are retained.
- Desktop and 390 × 844 mobile previews were inspected. Product images fit their containers; there is no mobile horizontal overflow. Gravity's filter returns 29 eligible listings, Fasteners' filter 58, and the observed accessory/status entries are absent from filters.
- [Admission evidence](benchmarks/2026-11-03-source-admission.json), [cycling audit](benchmarks/2026-11-03-admission-cycling-merchant-audit.json), [tools audit](benchmarks/2026-11-03-admission-tools-merchant-audit.json), and [snow traversal](benchmarks/2026-11-03-skiessentials-pagination.json) retain the methods and limitations.
- Final standalone bundles are task-owned local artifacts under `.local/source-expansion/release-admission-20261103/{cycling,tools}-final-site/`. Fresh runner-side audits remain required at publication.

## Authorized action requested

1. Push the prepared branch to `lifan-builds/snow-deal`, create a pull request, and merge after required checks pass.
2. Run the existing cycling/tools refresh workflow with history restoration (`bootstrap_history=false`). Require complete refreshes, clean merchant audits and exact production snapshot hashes at `bigring.clifan.com` and `benchdrop.clifan.com`.
3. Run the existing full snow refresh/deploy workflow for `freshpowder.clifan.com`, preserving the previous public snapshot/history and checking source outcomes and the deployed freshness receipt.
4. Verify production discount ordering, source filters, image layout, history links, and accurate source limitations after deployment.

Existing eight-hour schedules will use the merged code. A failed source or unresolved audit blocks that catalog's release; it is not grounds to relax admission checks.

## Recovery and remaining gaps

If the new release fails, retain the existing production deployment. For a deployed regression, restore production baseline `0530cad` with a fresh validated snapshot and preserved history; old offers must still expire after 24 hours. Do not redeploy expired data as fresh.

Grizzly and MEC access remain unresolved. Ski Essentials listing recovery does not provide independently confirmed fit or checkout stock. Shipping, historical reference validity, broad competitor accuracy, the strongest mobile-speed comparisons, and thirty real observation days still need evidence. This release improves coverage and correctness; it does not satisfy the full all-competitor objective.
