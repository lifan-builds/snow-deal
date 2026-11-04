# Beaver Industrial Supply release

Status: candidate validation in progress; no source activation or publication yet.

## Scope

Add the verified sales-and-closeouts cohort to Bench Drop through the existing Shopify feed, with exact product-page purchase checks. Preserve percentage-first ranking, the $200 default retailer-reference floor, independent merchant audit, history restoration, source retention on partial refresh and exact live snapshot verification. Delayed or call-for-availability stock retains its notice and cannot pass the confirmed-stock filter. Explicit unavailable stock is excluded. Two abrasive packs that mention a sander are excluded before machine classification.

Bolton's tested candidate adapter is included for future evaluation but remains unconfigured because its active warehouse restriction does not identify product-level freight eligibility. Do not count Bolton as a retailer gain.

## Admission gate

Complete every configured Beaver feed page and eligible product-page check. Preserve prior incomplete candidate evidence. Independently audit the fixed top-ten plus seeded-twenty sample, supplemented by every qualifying offer at least 40% off. Check exact prices/reference, selected variant, stock, currency and purchase destination. Confirm the normal storefront stock/shipping disclosures without cart or checkout actions. Record final counts separately from the preliminary stock-blind 157/15 result.

## Approved rollout

The user's standing approval covers comparable tested and audited releases. After admission, enable only the observed source cohort, run offline tests and CI, publish a branch PR and merge after passing checks. Dispatch the existing cycling/tools refresh with bootstrap disabled; restore previous release assets, preserve observation history and allow its complete-source/merchant gates to determine publication. Verify both workflow outcomes, the tools snapshot hash, every configured source outcome, Beaver filtered cards and new source stock labels. Fresh Powder requires no new scrape for this tools-source change.

## Recovery

If candidate admission fails, keep the source disabled and retain the failure. If production refresh or audit fails, inspect the recorded failed gate before any retry; never bypass it or reset timestamps. If an activated source becomes misleading, remove its catalog configuration in a tested corrective release and run the normal audited publication. Preserve previous release assets/history and actual dates. Do not restore an old snapshot under a new successful observation time.
