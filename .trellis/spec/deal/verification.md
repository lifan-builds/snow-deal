# Verification

## Safe default checks

Run offline checks from the repository root:

```bash
python -m pytest aggregator/tests/ -x -q
python -m compileall -q snow_deals aggregator/aggregator api app.py
git diff --check
```

Tests must use temporary databases and explicit dummy environment values where required. Do not let validation discover or load the repository `.env` or existing database files.

For parser changes, add deterministic HTML/config fixtures covering valid products, exclusions, whole-dollar and decimal prices, categories, brand, images, and malformed input. Live selector checks with browser tooling require explicit task scope and must not persist cookies or browser state.

Migration validation is offline only: template hashes, TOML/JSON parsing, bounded hook fixtures, Python syntax, unit tests, staged-path review, and added-line credential-signature review.
