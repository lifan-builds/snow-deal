# Implementation status

Boundary: ingestion currently canonicalizes explicit catalog aliases, while
query/filter/form state and exact history matching still use stored spellings.
The common identity helper will accept the catalog's existing alias tuple and
serve those existing paths consistently. Query cards/facets and history template
context will be projected copies; source rows, offers, databases, observations,
timestamps and health/fingerprint inputs stay raw and unchanged.

Expected files: common identity, ingestion normalization, optional query and
history alias inputs, web wiring, and focused common regressions. Empty-alias
query callers retain their current behavior. Root owns catalog alias tables,
evidence, public-data replay, review and publication. No source, schema, money,
ranking, size, free-text raw-brand matching, network or operational-data changes.

Implementation is stable for independent review. Tests use synthetic exact alias
tables and temporary databases only; no public/operational database was opened
by the implementer. Root has been notified of the interface and stable checkpoint.

## Implemented

- `common/deal_common/catalog/identity.py`: optional keyword-only
  `brand_aliases: tuple[tuple[str, str], ...] = ()` applies the existing exact
  case-folded lookup after fulfillment-label rejection. No suffix removal,
  fuzzy matching, retailer inference or recursive alias resolution.
- `refresh.py`: ingestion calls that helper with `catalog.brand_aliases`, replacing
  its separate lookup while retaining original Product objects and offer facts.
- `query.py`: the same optional keyword projects canonical card/facet brands and
  resolves legacy requested labels before filtering, counts and pagination.
  Matching still searches raw merchant brands; canonical display names are also
  searchable. Source rows, filters and offers are never rewritten. Empty alias
  inputs preserve existing query semantics, including raw exact filters and the
  no-search short circuit. Ranking and selected-variant logic are unchanged.
- `web.py`: catalog aliases flow into query and history; known requested aliases
  select the canonical option, applied-filter label and pagination URLs. Unknown
  requests retain the existing selected escaped empty-result behavior. History
  template context uses a projected brand label; health receives raw sources.
- `storage.py`: `read_offer_history(..., brand_aliases=())` compares historical and
  current manufacturer labels through the same helper. Source, product name/URL,
  variant ID/options/destination and daily-history guards remain exact. The
  database/history contents and timestamps are never changed by reads.
- `common/tests/test_manufacturer_filters.py`: 25 regression cases cover a
  35-product alias group spread across three spellings/two stores/two pages;
  exact selected M-variant price/reference/options/stock/destination; budget
  filtering; stable source-order-independent unrestricted order; no-alias
  behavior; raw brand text searches; distinct subbrands/unknowns; saved URLs,
  pagination and escaping; health fingerprint/database bytes; history both
  before and after later ingestion; every other exact history guard.

## Checks

- Before implementation: **24 failed, 1 passed** in the new focused file,
  including actual legacy form-selection and history-route failures in addition
  to the missing optional interface.
- New and existing catalog runtime regressions: **72 passed**.
- Full offline `scripts/check.py -q`: **928 passed** (903 baseline +25 new),
  eight unchanged deprecation/key-length warnings.
- Exact existing CI Ruff scope plus the new test file: **passed**.
- `git diff --check`: **passed**.

## Handoff

Root owns the verified real cycling/tools alias tables, public-snapshot replay,
independent review and publication. Synthetic test maps deliberately avoid
guessing those manufacturer relationships. No catalog configuration, source,
schema, ranking, history retention or deployment was changed by this implementer;
no network, credential, commit or push action was performed. The current code is
ready for those root-owned checks; no further production edits are planned.
