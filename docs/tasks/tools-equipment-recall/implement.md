# Implementation and validation

1. Capture failing positive regressions from the exact merchant examples and counterexamples from accessory-only, replacement, consumable and contradictory-taxonomy inputs.
2. Make the small tools-owned classification correction. Preserve all existing negative gates and exact selected-offer handling. Add an integration regression through normalize/query if needed to prove price/stock/destination binding.
3. Run focused tools tests, full offline checks and scoped Ruff. Record failed-before/pass-after evidence and all affected files. Independent full-scope review follows.
4. Root reconciles retained raw feeds, independently checks every newly admitted selected offer, and runs the actual complete candidate refresh plus the existing timed merchant audit. Failed/inconclusive evidence remains retained.
5. Publish only this correction after review/CI/admission under standing approval; execute the existing audited tools refresh/deploy workflow and verify public snapshot/hash, history and relevant filters. Keep House candidate on its separate local branch.
