# Implementation status

Boundary: the observed Contender #MWS Options variants are not ordinary shopper
size choices and cannot be merged into their otherwise matching bases. Add a
small exact-host predicate in the existing Shopify parser, use it before offer
construction and reuse it for independent audit rejection. No stripping, alias
mapping, price/stock transfer, generic size normalization or history rewrite.

Owned changes: shared Shopify parser, catalog audit, focused factual regression
fixtures/tests, parser contract and Trellis mirror, plus this implementation
record. Root owns full source capture/replay, refresh/admission and publication.
No network, operational DB, source configuration, commit or deployment actions;
Circle/root work remains untouched.

Implementation, tests and contracts are stable and handed to independent review.
Runtime files have remained unchanged since root started its live merchant audit.

## Implemented

- `common/deal_common/parsers/shopify.py`: add the small exact-host
  `is_contender_generated_variant(variant, url)` predicate. It checks only
  Contender apex/www and the bounded literal `#MWS Options <digits>` marker in
  variant title/option1–3 or a product.js options list. Skip marked records before
  money, size, stock, image and offer construction; generated-only products drop
  through the existing no-offers path. No field stripping, ID mapping, inferred
  base or price/reference/stock transfer.
- `common/deal_common/catalog/audit.py`: reuse the predicate on the independently
  fetched selected variant. A marked row receives `ordinary_variant: false` and
  cannot be a match even if its endpoint money/stock agrees. Ordinary variants
  and other hosts retain their prior check set and result shape.
- `common/tests/fixtures/contender_generated_options.json`: four reduced factual
  products/fourteen generated+ordinary variant records covering all seven
  merchant comparisons. No long descriptions, scripts or private state.
- `common/tests/test_contender_generated_options.py`: 24 cases cover exact
  surviving fields, actual reference inflation/full-price base and false-stock
  examples, generated-only products, synthetic extreme reference/ghost rows,
  rank/count/pagination/size selection, unknown ordinary stock, apex/www and
  foreign-host isolation, ordinary MWS words, every variant marker field and
  independent generated-old-offer rejection with ordinary audit preservation.
- Append the source-specific parser/audit contract to
  `docs/project-guidance/aggregator-data-and-parsers.md` and its Trellis mirror.

## Verification

- Focused new parser and existing merchant-audit tests: **36 passed**.
- Full shared offline `scripts/check.py -q`: **1226 passed**, eight existing
  deprecation/key-length warnings. This shared run includes inactive Circle WIP;
  root separately reports the isolated clean release tree passing1133 tests.
- Exact CI Ruff scope plus the new test file: **passed**.
- Extended Shopify Ruff comparison: the same four inherited findings before and
  after (TRY004 and three FURB167); no new finding was introduced.
- `git diff --check`: **passed**.

Root's complete retained-source replay independently reports exactly seven
generated offers removed, all524 ordinary offers identical, 183→182 accepted
products, twenty other current source rows unchanged and all58 prior history
observations retained plus one actual Contender source observation. No new source
or competitive score is claimed. The implementation's four-product fixture
independently verifies the actual ordinary IDs/prices/stock/options/destinations;
the full replay remains root-owned evidence.

## Final handoff

Independent reviewer confirmed the shared full suite/CI scope and retained-feed/
public-task-snapshot replay with no runtime findings. All owned code, tests and
contracts are complete; no further runtime edits are planned. Root owns the
still-pending live merchant audit, source/history release receipt, publication,
clean packaging and production verification. Existing historical generated rows
are retained; current browsing changes only with the validated fresh source
replacement and deployment.

No network, operational database, credentials, source configuration, schema,
ranking, UI architecture, commit, push or deployment action was performed by the
implementer. Root staging/PLANS and unrelated inactive Circle work are preserved.
