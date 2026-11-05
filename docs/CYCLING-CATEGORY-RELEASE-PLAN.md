# Cycling category precision

This release corrects two observed category errors: a glove admitted under generic Bike taxonomy, and explicit frame taxonomy treated as a complete bicycle or dropped entirely. The cycling classifier and its regression tests own the change. Percentage-first ranking, source transport, purchase identity, stock handling, and history policy remain unchanged.

The [task artifacts](tasks/cycling-category-precision/prd.md) define the scope and [primary evidence](tasks/cycling-category-precision/research/primary-evidence.json) records the observed products and retained feed captures. Research capture timestamps are not fresh stock evidence.

## Release gates

1. Independently review the entire change, run the offline suite and CI lint, and reconcile every changed classification in the retained feeds and existing public snapshot.
2. Restore the latest public cycling release asset into an explicit candidate. Refresh all twenty configured sources with existing request budgets and pacing; require complete collections and no source errors.
3. Check the default top-ten plus seeded-twenty sample and every newly eligible or reclassified in-stock listing, including those below the default reference floor. All merchant checks must match within the existing fifteen-minute audit window. Separately inspect affected product/package evidence.
4. Preserve prior-day observation rows exactly. Replace same-day rows only under the existing latest-successful-daily policy. Package the exact audited candidate and verify its rows and history.
5. Under standing release authorization, publish reviewed code for CI in parallel with fresh admission checks. Merge after CI, preview and admission checks pass, and reconcile active refresh jobs before updating the public cycling history asset. Deploy the exact bundle to the existing Big Ring project and verify its live hash, filters, frame classification, glove absence, and history pages.

Only cycling data is refreshed for this release. Tools and snow data are not part of the update. No account, credential, paid-plan or DNS changes are required.

## Recovery

Retain the prior public cycling asset and the last verified production deployment. If the new candidate fails any gate, do not upload or deploy it. If live verification fails after deployment, restore the previous verified Big Ring deployment and public cycling asset, then reconcile both hashes before another attempt. Preserve failure receipts and their actual timestamps.

This category correction is measurable progress, not evidence of an all-metric lead over competitors. Inventory counts, classifier-only differences and independently checked samples must remain distinct in the rollout receipt.
