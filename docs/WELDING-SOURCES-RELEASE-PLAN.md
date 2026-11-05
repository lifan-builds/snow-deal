# Welding equipment source expansion

Bench Drop gains Baker's Gas and Cyberweld through the existing bounded Shopify ingestion path. Precise equipment taxonomy admits welding power sources and plasma cutters while excluding standalone guns, wire feeders and feed units. Shared source-specific stock evidence keeps explicit backorders and negative stock tags out of confirmed-stock results. Manufacturer aliases combine equivalent Miller, Lincoln and Hobart labels without merging offers.

## Release gates

1. Complete independent code and retained-input review, full offline checks and CI. The review found a mislabeled CK wire-feed unit; preserve the initial admission receipt and rerun Baker's after correcting that classification.
2. Require complete USD collection traversal and passing top-ten plus seeded-twenty merchant audits, including every deep listing, for both new sources. Separately verify the observed Hobart backorder remains unknown rather than confirmed stock. Keep the existing fifteen-minute audit window and two-second pacing.
3. Refresh all eleven existing tools sources with current budgets. Reconcile accepted products against the review correction. Import the two audited new-source snapshots with their actual observation timestamps, without restamping. Audit the combined default sample and any new or reclassified existing-source stock listings.
4. Preserve prior-day history exactly and follow the existing latest-successful-daily replacement policy. Package the exact candidate and compare source and history rows.
5. Under standing release approval, publish reviewed code for CI. Merge only after CI, preview and data gates pass. Reconcile active refresh jobs, publish the validated tools asset, deploy the existing Bench Drop project, and verify the live fingerprint, retailer filters, exact variants, backorder display/exclusion and history pages.

The new retailers' listing counts are merchant listings, not unique models. The only preliminary ≥40% offer is also advertised at the same current price by its manufacturer; it is not an exclusive price advantage or independently verified historical low. See the [task](tasks/welding-sources/prd.md) and its research receipts. Baker's equipment breadth alone does not increase the useful-deep-retailer metric.

## Recovery

Retain the previous public tools asset and verified Bench Drop deployment. Any failed admission blocks publication. If production verification fails, restore both previous deployment and asset, verify their identities, and preserve failure evidence. No credential, DNS, paid-plan or account changes are part of this release.
