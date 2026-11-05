# Implementation status

Boundary: existing generic Sporting Goods taxonomy does not identify Incycle's
complete bikes. Interpret only the observed BICYCLES plus MOUNTAIN/GRAVEL/ROAD/
ACTIVE tags, or explicit TURBO & ELECTRIC BIKE, on exact HTTPS www.incycle.com
product URLs with exact Sporting Goods type. Existing frameset classification
stays first and unchanged. Guard newly admitted complete bikes against accessory
primary titles; retain all earlier condition/kids/shipping/accessory gates.

Expected owned paths: cycling classifier, focused tests/compact public fixtures
and this status. Root owns full feed classification review, fresh source/admission
and any source activation/fee copy. Circle reviewer owns its parser/tests; those
paths are untouched. The shared branch is currently codex/circle-exact-offers,
reported to root; the implementer will not change branches or stage other work.

No common parser, size inference, source/config activation, schema, ranking,
network, operational DB, credential, commit or deployment changes.

## Implemented and stable

- `catalogs/cycling/src/cycling_deals/catalog.py`: after the existing unchanged
  frameset branch, require exact HTTPS `www.incycle.com` product origin/path and
  exact normalized `Sporting Goods` taxonomy. Explicit `TURBO & ELECTRIC BIKE`
  identifies electric bikes before mountain discipline; `BICYCLES` requires an
  observed MOUNTAIN/GRAVEL/ROAD/ACTIVE tag. Missing or unobserved discipline cannot
  borrow a model/title inference inside this source-specific branch.
- Keep this as a small direct source condition rather than a new classification
  framework/helper. Reuse the existing accessory pattern for the source's primary
  title, preserving explicitly included accessory suffixes and rejecting an
  accessory that mentions a bike later. The existing global accessory-kind test
  uses the same unchanged expression, so other retailers' interpretation is not
  widened.
- `common/tests/fixtures/incycle_bicycles.json`: compact seven-product public feed
  subset for active/electric/mountain/road/gravel, the Default Title Pivot and the
  already-recognized Scott Frame & Fork. Keep full tags/option definitions plus
  representative actual available/unavailable variants; this reduced fixture is
  not a complete source feed or a live inventory receipt.
- `common/tests/test_incycle_classification.py`: 41 focused cases cover exact host,
  protocol and product path; generic/missing/unobserved tags; real category
  examples; electric/frameset precedence; accessories and misleading suffixes;
  condition/kids/shipping; included accessories; exact parser/normalization/query
  binding; raw-input preservation and Default Title size non-inference.

The existing frameset branch intentionally remains unchanged, per root's minimal
scope decision. Source-wide primary-product review before admission remains
root-owned; this patch does not claim a global repair to previously recognized
frame cases or other retailers' taxonomy.

## Verification

- New tests before implementation: **9 failed, 32 passed**. Six observed complete
  bikes were omitted; normalization retained only the preexisting frameset. The
  misleading accessory suffix and legitimate included-accessory case also
  demonstrated their distinct expected behavior.
- New plus existing cycling/lightweight taxonomy tests: **166 passed**.
- Full offline suite on the current shared worktree: **1086 passed**, eight
  existing deprecation/key-length warnings. This includes concurrent Circle
  reviewer changes, which the implementer did not alter.
- Exact CI Ruff scope plus the new test file: **passed**.
- `git diff --check`: **passed**.

Retained full public feed sanity check (no network or DB): all 87 raw products
classify as 19 framesets, 36 electric, 8 mountain, 5 gravel, 9 road and 10 other
complete bikes. The unchanged production Shopify parser/normalizer retains 86
products, with eight road bikes and the other category totals unchanged. That
is 67 parsed complete-bike additions over the prior 19 framesets; these are
retained-input counts, not fresh admission. Root owns the complete source and
merchant reconciliation.

The Sirrus fixture keeps variant43524025319555, USD799.97 /1599.99, XXS and its
full raw color/options/destination. Pivot's Large title keeps an empty exact-size
field because its purchasable variant is Default Title; Large queries cannot
match it. No prices, raw taxonomy, stock, variants, sizes or timestamps are
rewritten by classification.

## Handoff

Root was notified of runtime stability before full checks so its isolated source
probe can proceed. No further classifier/test edits are planned without
coordination. Independent review, live source completeness/currency/audits,
frameset shipping-policy evidence and product-specific exceptions, optional
source/fee-copy activation, history-preserving refresh and publication remain
root-owned. No assertion of thirteen explicit Ship to Home panels or checkout
totals is made here.
