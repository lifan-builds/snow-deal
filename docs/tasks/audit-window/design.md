# Bound merchant audit observations

The fixed M3 method requires merchant checks within 15 minutes of the displayed sample, but the shared auditor currently reports late matches. Add a 15-minute wall-clock window to `audit_sample`, stop further merchant reads when it expires, and stamp checks when they finish. Overdue or backwards-clock evidence is inconclusive so the existing CLI release gate fails. Preserve raw check facts when available; do not modify prior receipts.

Scope: shared audit transport/result recording, deterministic clock-controlled regression tests, and the parser/verification contract. Existing price, SKU, shipping, pagination and source-admission logic remain the same. The already-green PR #8 stays on its frozen release ref while this correction is prepared separately.
