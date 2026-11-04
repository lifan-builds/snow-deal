# Beaver Industrial Supply and RA Cycles release

Status: Beaver passed admission and is configured locally. RA Cycles remains disabled pending a complete, timely merchant audit. No publication yet.

## Scope

Add the verified sales-and-closeouts cohort to Bench Drop through the existing Shopify feed, with exact product-page purchase checks. Preserve percentage-first ranking, the $200 default retailer-reference floor, independent merchant audit, history restoration, source retention on partial refresh and exact live snapshot verification. Delayed or call-for-availability stock retains its notice and cannot pass the confirmed-stock filter. Explicit unavailable stock is excluded. Two abrasive packs that mention a sander are excluded before machine classification.

Bolton's tested candidate adapter is included for future evaluation but remains unconfigured because its active warehouse restriction does not identify product-level freight eligibility. Do not count Bolton as a retailer gain.

RA Cycles is also under admission review for Big Ring. Its normal bikes collection completed three feed pages and 144 product/evidence pairs. Exact stock checks yield 116 qualifying in-stock listings and 64 deep discounts; feed-only counts were provisional. Exact per-variant inventory distinguishes immediate stock from virtual-warehouse delivery. Preserve final-sale restrictions, give explicit Frameset taxonomy precedence, and retain numeric-s sizes as distinct literal labels. No RA activation occurs before a fresh complete detail-aware candidate and merchant audit.

The two source-specific paths add paced product/evidence requests. Increase the existing refresh job timeout from 30 to 45 minutes to accommodate that work; all completeness, audit, history and publication gates remain required.

## Admission gate

Complete every configured Beaver and RA feed page and eligible product/evidence check. Preserve prior incomplete candidate evidence. Independently audit the fixed top-ten plus seeded-twenty sample, supplemented by every qualifying offer at least 40% off. Check exact prices/reference, selected variant, stock, currency and purchase destination. Confirm the normal storefront stock/shipping disclosures without cart or checkout actions. Record final counts separately from the preliminary stock-blind 157/15 result.

## Approved rollout

The user's standing approval covers comparable tested and audited releases. After admission, enable only the observed source cohorts, run offline tests and CI, publish a branch PR and merge after passing checks. Dispatch the existing cycling/tools refresh with bootstrap disabled; restore previous release assets, preserve observation history and allow its complete-source/merchant gates to determine publication. Verify both workflow outcomes, both snapshot hashes, every configured source outcome, Beaver and RA filtered cards, exact sizes and stock/shipping labels. Fresh Powder requires no new scrape for this cycling/tools source change.

## Recovery

If candidate admission fails, keep the source disabled and retain the failure. If production refresh or audit fails, inspect the recorded failed gate before any retry; never bypass it or reset timestamps. If an activated source becomes misleading, remove its catalog configuration in a tested corrective release and run the normal audited publication. Preserve previous release assets/history and actual dates. Do not restore an old snapshot under a new successful observation time.

## Candidate evidence

Beaver completed three pages and 192 purchase-panel checks, yielding 75 qualifying in-stock listings and seven deep discounts. Independent top-ten plus seeded-twenty checks passed 30/30, including all seven deep deals. Unknown delayed stock is retained with its notice but excluded from confirmed-stock results.

RA captured 292 successful responses, including 144 HTML/JSON product pairs. Seven execution gaps of about 15 minutes occurred during capture; the cause is unconfirmed. Original observation times remain unchanged. Replaying those captured responses with the final decoder changed 122 notice strings and no prices, stock, identities or options. The first independent 76-offer audit returned 69 matches, zero mismatches and seven inconclusive results after a long execution gap crossed the 15-minute window. This is a failed gate, retained unchanged; admission requires a fresh complete audit.

The pre-release baseline is successful scheduled workflow `41789071208` at `cb200cb`: cycling 1,279 confirmed-stock listings / 115 deep deals, tools 583 / 24. Its public artifacts and dated observation history are retained for comparison.

A second local audit also expired (two matches, zero mismatches, 74 inconclusive) despite an idle-sleep assertion. Local execution continuity is unreliable; neither expired audit satisfies admission. The existing check workflow gains an opt-in, manual-only isolated candidate audit on a GitHub runner, using the same paced requests and 15-minute audit rule. It uploads public evidence only and has no deployment or data-release credentials. RA remains unconfigured pending that result.

A newer scheduled baseline, workflow `41868782908`, completed at 16:51 UTC on the same `cb200cb` code: cycling 1,232 confirmed-stock listings / 102 deep deals, tools 383 / 24. This supersedes the earlier baseline for rollout comparisons; market inventory changes are not attributed to this release.

## Fresh Powder build recovery

PR17 preview failed because the latest public snow snapshot pushed the function bundle to 230.75 MB, above Vercel’s 225 MB limit. The scheduled snow run `41833976108` also failed its production-snapshot verification after publishing the 13:25 UTC snapshot. An isolated compaction check reduced that 153,219,072-byte public database to 143,446,016 bytes with identical schema and every table’s full rows preserved. Add build-time compaction of the downloaded temporary snapshot only, after the existing migrations/review reconciliation. Do not alter source timestamps, delete history, compact operational/auth databases or change the explicit skip-download path. Verify a new provider build before merging, then verify the production snow snapshot as part of this release.

Provider preview `dpl_ChdLfUgGZfuXuxQb48d1rNiWFQRT` at `fe60d1b` reached Ready at 17:17:33 UTC. Its build log confirms the compacted 143,446,016-byte DB and unchanged latest observation, followed by successful dependency optimization/deployment. The full offline suite now passes 736 tests, including compaction failure atomicity. Production verification remains pending.

The follow-up build optimization removes only the proven duplicate `idx_history_url` from the temporary copy. Exact PRAGMA key comparison protects unexpected definitions. The public build copy becomes 125,919,232 bytes (27,299,840 bytes saved overall), with every table row preserved and history queries using the equivalent primary-key index. Default and exact-size serving query results are identical. Provider verification of this final optimization remains pending.
