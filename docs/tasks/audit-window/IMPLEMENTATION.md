# Merchant audit observation window

The Bike Closet admission audit matched its selected offers but ran longer than the benchmark's 15-minute comparison window. Previously the shared auditor stamped `checked_at` before fetching and could count a late response as a match.

The auditor now stamps completion and records the sample start separately. Any response outside the window is inconclusive even when all individual facts agree. No next endpoint starts after expiry; a backwards-clock observation permanently invalidates the window. Existing bounded network retries remain unchanged. The CLI already fails on any inconclusive result, so this applies to automated publication without a workflow exception.

Validation: 550 offline tests pass, including four deterministic deadline tests. Price, reference, variant, shipping and source logic remains covered by the existing suite. This change has no retrospective effect on saved audit receipts and does not by itself establish the timing of a displayed production sample.

Release after the tested Bike Closet follow-up merges. Require CI, then use the existing full refresh and exact deployed-snapshot checks. If a deadline fails, preserve the existing live snapshot and inspect the dated audit; do not increase the window merely to make a release pass.
