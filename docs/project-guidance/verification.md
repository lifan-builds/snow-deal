# Verification

## Safe default checks

Run offline checks from the repository root:

```bash
.venv/bin/python scripts/check.py -x -q
.venv/bin/python -m compileall -q common/deal_common catalogs/fresh-powder/src api app.py
git diff --check
```

Tests must use temporary databases and explicit dummy environment values where required. Do not let validation discover or load the repository `.env` or existing database files.

For parser changes, add deterministic HTML/config fixtures covering valid products, exclusions, whole-dollar and decimal prices, categories, brand, images, and malformed input. Live selector checks with browser tooling require explicit task scope and must not persist cookies or browser state.

Migration validation is offline only: template hashes, TOML/JSON parsing, bounded hook fixtures, Python syntax, unit tests, staged-path review, and added-line credential-signature review.

## Merchant audit timing

The shared merchant auditor records `sampled_at` when the audit starts, `check_started_at` for each offer, and `checked_at` when its result finishes. All observations must finish within 15 minutes of that sample. Late responses retain their factual checks but become inconclusive; expired audits stop starting further endpoint requests. An invalid backwards-clock observation permanently closes the window for that audit. Existing bounded retries may finish in flight, but cannot turn an overdue result into a passing check.

An inconclusive result fails the publication gate. Test deadline boundaries, completion timestamps, expiration between endpoints, and clock corrections with controlled clocks and mock transport. Do not rewrite earlier evidence. This deadline alone does not prove M3: a comparative accuracy claim also requires the corresponding displayed sample and the fixed benchmark's sampling and confidence rules.
