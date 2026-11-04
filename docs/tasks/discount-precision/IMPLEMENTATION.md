# Discount precision — November 4, 2026 UTC

A $2,220.10 Devinci against a $3,699 retailer reference is 39.98107596647743% off. Rounding before filtering incorrectly admitted it to a 40% minimum. The same rounding also let savings, lower prices or images break ties between genuinely different percentages.

The shared Product and VariantOffer now calculate percentages from decimal price inputs without presentation rounding. Cycling and tools already use this calculation before selecting a variant. Snow registers it in both list/count SQL connections and recomputes selectable and legacy percentages from prices, including in older read-only snapshots. No schema migration or history rewrite is required. Templates retain their existing formatting.

Fourteen new regressions cover just-below/exact/above thresholds, decimal boundary prices, invalid inputs, percentage ordering ahead of savings/images, correct selected URLs, exact-fit selection, counts and pagination. Nine failed against the prior implementation; all now pass. The full offline suite passes 573 tests, with four existing warnings. CI Ruff plus shared-model/new-test lint and whitespace checks pass. One existing clothing test fixture now supplies prices consistent with its intended 80% discount.

[Read-only recalculation evidence](../../benchmarks/2026-11-04-discount-precision.json) evaluates the downloaded public snapshots at their original measurement times. Cycling remains 1,159 eligible / 86 deep / 12 useful retailers; tools remains 607 / 24 / 5. evo remains 55 eligible, but has **two**, not three, offers at least 40% off. The Devinci is still eligible for unrestricted browsing. These are listing counts, not unique model counts. Earlier evidence remains historical; the original evo admission receipt used rounded percentages and must be read with this correction. No new merchant observation is implied.

The current PR #7 rollout completed successfully, with subsequent snow refreshes. Its [receipt](../../benchmarks/2026-11-04-source-quality-rollout.json) records actual outcomes and remaining limitations. The initial full snow run withheld The House after a count drop/incomplete traversal, and MEC returned HTTP 403. Ski Essentials completed all six collections, producing 906 discounted listings. Local follow-up page checks later hit TLS protocol errors; pipeline production timestamp verification and a subsequent public health read succeeded, but those do not establish an exact snow snapshot hash.

The additional Highland source probe had two complete collections (61 parsed products, eight classified), but clearance failed HTTP 503, so the source was incomplete and no rows were admitted. Ohio Power Tool still returned HTTP 403. Neither retailer is enabled. Revisit with complete evidence rather than treating these outcomes as empty catalogs.

## Publication

This change follows the frozen evo PR #10 and the earlier source/audit releases. Require green checks, then merge and run fresh audited deployments under standing approval. Preserve history and reject incomplete source/audit results. Keep the preceding verified deployment if any gate fails. Recheck percentage ordering and threshold behavior on each production site. Implementation and queued publication do not establish market leadership.
