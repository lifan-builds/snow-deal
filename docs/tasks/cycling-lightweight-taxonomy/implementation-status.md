# Implementation status

Boundary: cycling's accessory-kind regex interprets LIGHT in the observed
`BIKES AND FRAMES/BIKES - ELECTRIC/ELECTRIC MOUNTAIN LIGHT WEIGHT` branch as a
standalone light. Derive the accessory-check text from only that exact positive
branch in its observed parent context. Keep raw merchant taxonomy, descendants,
all other condition/kids/shipping/accessory checks and offer facts unchanged.

Expected changes: cycling classifier, focused common regression tests and this
status. Root owns merchant evidence, any buying-note copy, retained/public replay,
fresh source/audit checks and release. No parser, source, schema, manufacturer,
size, money, ranking or UI architecture changes. No network, credentials,
operational DB, commit, push or deployment actions.

Implementation is stable and handed back for independent review, root-owned
replay/admission and release. Root has been notified that its buying-note edit
can proceed; no further classifier/test changes are planned by the implementer.

## Changes

- `catalogs/cycling/src/cycling_deals/catalog.py`: derive `accessory_kind` by
  replacing only the exact root-context branch
  `bikes and frames/bikes - electric/electric mountain light weight` with its
  non-accessory description for the existing accessory regex. Require a slash
  or end after the complete segment. Preserve every negative descendant; do not
  whitelist model names, arbitrary Light words or unrelated category branches.
  Raw `kind` still feeds all other guards and the existing positive/category
  rules, and `Product.product_type` is untouched.
- `common/tests/fixtures/cycling_lightweight_bikes.json`: reduced public captured
  Heckler SL CC X0 Transmission Reserve, Habit Neo1 and Shuttle SL Pro X0
  Transmission records, with their original taxonomy, brand/tags, option metadata
  and exact variant price/reference/stock/option IDs. No merchant description or
  checkout content is needed in the fixture.
- `common/tests/test_cycling_lightweight_taxonomy.py`: 23 regressions cover those
  complete bikes; accessory descendants and actual Bike Lights; unrelated or
  prefix-similar Light Weight kinds; apparel-primary, demo/kids and negative
  shipping/condition tags; parser→normalization→query exact-offer binding.

The exact captured in-stock Heckler selection remains variant44649480650821,
XX-Large / Gloss Magenta, current4499.77 / reference11699.99 and the matching
currency/variant destination. Sold-out Medium variants cannot satisfy fit.
All three fixture products retain raw source_category values and offer data;
the normalized query keeps percentage-first ordering. These are retained-input
regressions, not assertions of live inventory or checkout totals.

## Checks

- New tests before the production patch: **4 failed, 19 passed**. All three real
  positive classifications returned None and production-path normalization
  returned zero products, demonstrating the observed failure.
- New plus existing cycling tests: **124 passed**.
- Full offline `scripts/check.py -q`: **951 passed** (928 baseline +23 new),
  eight existing deprecation/key-length warnings.
- Exact CI Ruff command plus the new test file: **passed**.
- `git diff --check`: **passed**.

## Handoff and limits

Root owns the all-feed/public-snapshot classification reconciliation, independent
review, fresh source traversal, separate merchant samples/all-recovered checks,
checkout/closeout disclosures, history-preserving full refresh and publication.
The implementer read only the explicitly authorized captured public feed for
fixtures and used temporary/offline tests. No network, operational database,
credential, catalog source/schema/alias/money/size/ranking, commit, push or
deployment action was performed.

## Independent review correction

Review added a failing-before singular BATTERY descendant case and broadened the existing battery accessory term to cover singular and plural forms. Final checks pass 24 focused lightweight cases and 952 full-suite tests. All 174 raw records and 171 parsed records retain the same classifications/normalized outputs as the initial patch; the 13 recovered listings and every original offer field are unchanged. See review-status.md for the final gate.
