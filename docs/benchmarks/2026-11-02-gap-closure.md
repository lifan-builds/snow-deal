# Gap closure — 2 November 2026

This records improvements and unresolved evidence, not an all-competitor win. The [current matrix](2026-11-02-gap-matrix.md) covers 20 competitors. The initial matrix and earlier successful audits remain intact.

| Measure | Earlier snapshot | Latest snapshot |
|---|---:|---:|
| Cycling, in-stock offers above $1,000 reference | 250 | 309 |
| Cycling, offers at least 40% off | 33 | 32 |
| Cycling, retailers contributing deep offers | 2 | 3 |
| Tools, in-stock offers above $200 reference | 71 | 175 |
| Tools, offers at least 40% off | 4 | 7 |
| Tools, retailers contributing deep offers | 1 | 2 |
| Maximum browsing offer age, all three apps | 72 hours | 24 hours |
| Prepared refresh interval | Snow daily; new catalogs manual | Every eight hours, pending publication |

These are merchant-reported listings, not unique models, landed prices or independently verified former selling prices. Cycling briefly had 311 listings before the subsequent refresh returned 309. Its deep-deal count fell despite an additional retailer; inventory changes must not be attributed to code improvements.

## Merchant evidence

| Catalog/check | Matches | Mismatches | Inconclusive | Disposition |
|---|---:|---:|---:|---|
| Cycling, expanded first audit | 30 | 0 | 0 | Exact selected endpoint facts matched at that time |
| Cycling, final repeat | 27 | 0 | 3 | Bicycle Warehouse HTTP 429; stopped that host |
| Tools, expanded first audit | 30 | 0 | 0 | Includes Tool Nut and Woodcraft |
| Tools, final repeat | 17 | 0 | 13 | Tool Nut HTTP 429; stopped that host |
| Snow, reconciled audit | 22 | 0 | 8 | Ski Pro AZ / Blauer checks blocked; five auditor-only MSRP-option mismatches resolved with separate rechecks |

Top ten plus twenty seeded random offers; seed 20261102. Reports record selected prices, references, options, destinations, timestamp, response digest and allowed public merchant fields. Fresh anonymous currency responses are reduced to currency only; no session/cart contents are retained. Snow's eligible population remained 969 and its sampled URLs were unchanged after correcting latest-store/24-hour cohort constraints. Original snow mismatch evidence and the five separate rechecks are preserved.

Unknown is not a pass or a proven wrong offer. A 30/30 sample does not establish 99% population accuracy. These endpoint checks also do not establish checkout availability, full package contents, new condition or historical reference validity. Accordingly M3/M4 remain observed evidence, not measured full-metric wins. Later rate limits are retained rather than replaced with the earlier passing sample.

## Implemented gap fixes

- Added complete, USD-verified Bicycle Warehouse and Tool Nut source collections. Tool Nut's broad sale feed hit its pagination cap and was rejected; only fully traversed narrower collections were enabled.
- Corrected portable band saws versus stationary machines and explicit manufacturer aliases, including JET/Jet Tools, Kreg/Kreg Tool, SawStop/Sawstop and Liv/LIV. No fuzzy cross-model deduplication.
- Browsing, snow facets and counts exclude offers older than 24 hours and future timestamps. Snow's health timestamp cannot be renewed by an unsuccessful attempt.
- History now restores before each refresh, survives packaging and is retained as one actual successful observation per UTC date for 45 days. A missing previous snapshot requires explicit first-run bootstrap; failed downloads never create an empty-history replacement.
- New release workflow requires merchant audit success and verifies the exact public snapshot hash after deploying the standalone bundle. Failed audit artifacts are preserved. Vercel project IDs and public URLs are required before publication.
- M10 rejects fewer than three production runs, absent CLS evidence and our CLS above 0.1. Missing competitor data remains missing.

## UI and verification

At 390×844, Big Ring's first full price ends at 706.3 px and Bench Drop's at 738.3 px: zero initial scroll, no horizontal overflow. Budget plus exact fit/package took four meaningful actions. Medium bikes under $2,000 returned 33; bare tools under $250 returned six. These are functional local checks, not controlled human conversion studies. Current history UI correctly says one observed day; it makes no historical-low claim.

307 offline tests pass, including failing-restoration safeguards, source identity, incomplete-refresh retention, exact variant destinations, 24-hour expiry, daily history retention and wrong-live-snapshot rejection. Scoped Ruff, JavaScript syntax, YAML parsing and diff whitespace checks pass. Both real standalone bundles served their expected catalog, source pages, CSS, sitemap and matching receipt hash in isolated smoke tests. PyYAML and actionlint were unavailable; YAML was parsed with Ruby's standard YAML library, not represented as full Actions semantic validation.

## Open gaps and next evidence

1. Coverage: tools now has seven deep offers, still a small catalog. Acme, MyToolStore, Authorized Tool Outlet and JB Tools blocked probes. Do not bypass them; authorized partner feeds or accessible complete collections are the next sources. City Grounds is not enabled because e-motos and ambiguous wheel/frame sizing require more work. Empty/partial feeds never inflate counts.
2. Merchant reliability: wait for retailer cooldown or obtain permitted feed access before new audits. Both new catalogs' latest repeat audits are inconclusive, so their publication gates currently fail. Do not weaken the gate for launch.
3. Comparable competition: full representative merchant, condition/package and inventory audits across all competitors remain incomplete. [HardHat Deals](https://hardhatdeals.com/) was added after observing 407 broad offers and trade/reference controls; its broad count is not M1.
4. History: at least 30 real observed UTC dates are needed. Repeated checks today cannot close M8. No recurring collection is live for the new catalogs yet.
5. Production: create/configure the new projects and domains, publish only after gates pass, then collect three comparable cold LCP/CLS runs. Local geometry is not production performance.

The [release plan](../CATALOG-RELEASE-PLAN.md) defines the exact approval scope. No new code, databases, deployment or schedule was published during this work. Strict leadership remains unproven; zero-scroll or 100% ceilings can only tie when a competitor also reaches them.
