# Implementation status

Boundary: preserve Contender's exact contact-for-current-price caveat as optional
price_note metadata on each offer. Keep price/reference/stock/fit/identity and
query behavior unchanged. Independently audit the source note; display it beside
the selected price and its details, and project it only from each dated history
candidate (empty for old observations). No current-note backfill or schema change.

Expected runtime paths: shared offers, Shopify decoder, catalog audit/storage and
card/history templates. Reuse existing styles. Focused tests and mirrored parser/
web contracts are owned here; root owns research/replay/refresh/audits/publication.
Circle and prior root receipts/PLANS remain untouched. No network, operational DB,
credentials, commit or deployment actions by implementer.

## Completed implementation

- `common/deal_common/offers.py`: append optional `price_note=''` to preserve
  existing constructors. No schema migration.
- `common/deal_common/parsers/shopify.py`: decode the exact
  `contact-for-current-price` tag (list or comma-separated string) only on
  Contender's apex/www hosts. Bind the fixed factual note to each affected
  variant without changing eligibility, money, stock or generated-option guards.
- `common/deal_common/catalog/audit.py`: decode current product.js tags
  independently and compare with the selected stored note whenever either is
  nonempty. Both-empty ordinary/legacy audits retain their previous result shape.
- `common/deal_common/catalog/storage.py`: project only each dated candidate's
  optional note. Missing historical fields stay empty; never inherit today's
  note or change identity/daily retention.
- Shared card/details/history templates: render normal escaped notes beside the
  selected price and within the corresponding dated history price cell. Reuse
  existing styles. Explain that retailer pricing notes appear only when recorded.
- Mirrored parser and web/deployment contracts document these rules. The parser
  contract/mirror also require raw-product membership and exact variant
  price/stock checks before explaining a normalized listing's disappearance.

`common/tests/test_merchant_price_notes.py` adds 27 regression cases using the
existing reduced Contender fixture. They cover source/tag boundaries, legacy
constructors, price/stock/fit/ranking/count/page invariance, independent missing
or changed note audit failures, and escaped selected-card/detailed/history
rendering. Historical observations retain their own note or absence; synthetic
database bytes are unchanged by reads/rendering. Existing generated-option audit
tests now isolate that predicate from note agreement, and the legacy history
projection expectation includes the additive empty field.

## Checks

- Read-only baseline/current parser replay on factual XL variant
  `43266977104117`: baseline omitted the note; final parser retains the fixed
  note. All other offer fields compare exactly, including $1,799/$3,400,
  `in_stock`, XL and the exact variant destination. No network or database used.
- Focused safe check of pricing-note, generated-option and catalog-runtime tests:
  **98 passed**.
- Full `python scripts/check.py -q`: **1,253 passed**, eight existing warnings,
  in 5.93 seconds. This shared-worktree run includes unrelated inactive Circle
  tests; no Circle files were changed.
- Exact catalog CI Ruff scope plus changed offers/new/adjusted focused tests:
  **passed**. Extended Shopify lint matches HEAD exactly: one existing TRY004
  and three existing FURB167 findings, no new findings.
- `git diff --check`: **passed**.

## Handoff

Runtime was declared stable before root's complete-feed replay and merchant
audit. The only later runtime-path edit was the root-approved explanatory
history sentence; parser/model/audit behavior stayed fixed. Tests/contracts are
stable and handed to the independent reviewer. Root owns retained-feed replay,
live merchant audit, prepared snapshot, UI/live verification and publication;
those gates are not claimed complete by this implementer. No network,
operational database, credential, commit, push or deployment actions were taken.
