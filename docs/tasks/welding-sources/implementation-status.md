# Implementation status

Boundary: welding power sources and plasma cutters are currently omitted, while
the shared Shopify path can confirm stock despite the captured Baker's backorder
notice or Cyberweld negative stock tag. The tools classifier owns equipment
identity; a source-scoped shipping-notice dispatcher will serve both ingestion
and the independent product audit. Harvey's decoder stays unchanged.

Expected changes: tools classifier and focused classification tests; the shared
notice dispatcher plus its two existing consumers; deterministic availability
fixtures/tests; retained-feed and explicit public-snapshot replay receipts here.
No retailer activation, schema/history/ranking changes, live
requests, credentials, commits or publication.

Root subsequently delegated three explicit manufacturer aliases after matching
part numbers across the two feeds and primary pages (research/brand-aliases.json):
Miller Electric → Miller, Lincoln Electric → Lincoln, and Hobart Welding Products
→ Hobart. They use the existing normalization mechanism; raw Products and stored
history remain unchanged. A cross-retailer brand-filter regression binds each
selected offer to its own variant, price and destination.

Implementation is stable and ready for independent review/source admission.
Root has been notified; no source was activated by the implementer.

## Changes

- `catalogs/tools/src/tool_deals/catalog.py`: recognize explicit welding-machine
  and plasma-cutting taxonomy, precise machine tags, and declared-manufacturer
  machine tags on explicit fixed bundles. Negative condition/accessory taxonomy
  still runs first. Standalone gun/feeder tags and primary titles stay excluded,
  including the mislabeled Baker's ArcReach16 feeder. An explicit Wire Feeder
  Welder primary title retains the actual Lincoln machine despite its ambiguous
  Baker's Wire Feeder tag. Included `w/SpoolRunner`/`w/Intellx` suffixes have the
  same primary-identity boundary as spaced `with`/`including` phrases.
- `common/deal_common/parsers/availability.py`: share retailer-scoped evidence
  across ingestion and independently fetched merchant data. Baker's feed
  `body_html` and product.js `description` preserve the observed active
  `Machine is on backorder.` sentence on every variant. Cyberweld's explicit
  `auto_outofstock` tag withholds confirmed stock, including the actual
  `store.cyberweld.com` host. Harvey's original decoder is unchanged and remains
  the fallback.
- `shopify.py` and `catalog/audit.py`: switch only the shared notice import.
  Prices, references, options, variant IDs, destinations and direct-discount
  calculations are unchanged. No rebate or cart-only offer is manufactured.
- Tools tests, `common/tests/test_welding_availability.py` and a reduced captured
  Baker's fixture cover real packages, component precedence, both independent
  description formats, cross-retailer brand filtering and exact offer binding.
  The Cyberweld positive-availability conflict is labeled synthetic: all captured
  negative-tag variants currently report available=false.

## Verification

- Initial focused run before implementation: **17 failed, 136 passed**. Failures
  demonstrated omitted complete machines and stock incorrectly confirmed for
  the actual Baker's backorder and synthetic Cyberweld conflicts.
- Final focused tools/availability/unchanged-Harvey tests: **162 passed**.
- Full `scripts/check.py -q`: **903 passed**, eight existing deprecation/key-length
  warnings. No live requests or operational database access.
- Exact CI Ruff command plus the new decoder/tests: **passed**. Replay script
  Ruff and `git diff --check`: **passed**. Broader direct Shopify Ruff comparison
  improved five findings to four; the remaining TRY004 and three FURB167 findings
  are unchanged baseline code outside this behavior patch.

## Retained-input reconciliation

`research/classification-replay.py` writes the reproducible complete disposition
receipt `research/classification-replay.json`. It uses Git HEAD as the baseline,
the task-owned Baker's 414-product grinder-inclusive union and all 419 Cyberweld
records. The original 371-product capture is untouched. Every raw record has
before/after classification, its evidence and production-path eligibility;
all raw-input SHA values remain unchanged.

| Retained feed | Raw equipment classification | Discounted normalized before → after | Changes |
| --- | --- | --- | --- |
| Baker's 414 | 364 workshop, 41 power tools, 9 excluded | 7 → 207 | 200 added, zero removed; one existing Miller alias change |
| Cyberweld 419 | 321 workshop, 98 excluded | 0 → 215 | 215 added, zero removed |

The 98 excluded Cyberweld records are standalone gun/feeder taxonomy. Baker's
nine exclusions are a replacement charger, two cable liners, a MIG gun,
consumable electrodes, the standalone ArcReach16 feeder, the Cold Wire Feed Unit Model #5, an unrecognized Diamond
Cutting System primary identity and a cordless fan mislabeled Angle Grinders.
The latter two remain outside the current recognized primary-title rules; no
equipment identity was inferred from collection placement.

All parsed Product/offer fields compare exactly before/after except the single
Baker's backorder offer, whose availability changes from in_stock to unknown
with the retained notice. This is a 2499/2560 direct-price offer with unchanged
variant32158328258662 and purchase destination. The normalized brand change is
the already-recognized Miller XMT650 Stationary Package (Miller Electric→Miller).

At the $200 reference floor, the retained Baker's feed has 204 confirmed-stock
products and zero at ≥40%; Cyberweld has 215 and one respectively. Baker's has
206 in-stock offers plus one unknown; Cyberweld has 219 in-stock offers across
215 products. These are retained-feed counts, not fresh admission or checkout
verification, and no freshness timestamp is renewed by the replay.

The explicitly authorized public tools snapshot was opened through read-only
SQLite: **11 sources, 730 accepted products, zero classification/alias changes**.
Its SHA remains
`9d027e78072eac01b003efb7b54da6b9d6dfc21b4f49d37d7b743e66b8e5035c`.
Its normalized rows retain source_category but omit raw tags/rejected products,
so this replay cannot establish recall for previously rejected existing-source
products. Root's full fresh refresh and separate merchant audits remain required.

## Remaining handoff

Independent review, complete candidate traversal and timed merchant admission,
all-source fresh tools refresh/history checks and publication are root-owned.
The implementer has not enabled either source, changed schema/history/ranking,
read credentials, made network calls, committed, pushed or deployed.

## Independent review corrections

The reviewer found a retained Baker's standalone CK Worldwide Cold Wire Feed Unit Model #5 (WF5-023) mislabeled TIG Welding Machine. The component-title guard now includes Wire Feed Unit alongside Wire Feeder, including the Welder Wire Feed Unit construction. Explicit complete machines with included feed units and the SP-140T Wire Feeder Welder remain eligible. Two negative regressions failed before this fix; one included-unit positive locks in the primary-machine boundary. No other runtime change followed the implementation checkpoint.

A new normalization/query/daily-history regression verifies the exact Baker's variant and direct prices, raw versus canonical Hobart manufacturer, unknown-stock filtering, preserved prior-day notice and unchanged direct price after a later notice-free success. Replayed all 833 retained raw records against the pre-review checkpoint: only that Baker's component changes eligibility; Cyberweld is unchanged. The prior replay receipt is retained at .local/source-expansion/welding-20261105/classification-replay-pre-review.json and the current research receipt has the final classifier hash. Root restarted Baker's admission with the stable final code; earlier admission and research remain dated evidence. Independent review is in review.md.
