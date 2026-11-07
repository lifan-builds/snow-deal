# IOC taxonomy implementation

Added source-bound machine recognition in `catalogs/tools/src/tool_deals/catalog.py`. Only exact HTTPS `www.weldingsuppliesfromioc.com/products/` URLs can use the observed Welding/Cutting types and exact machine taxonomy. Existing title, component, condition and accessory-type guards run first. Accessories, parts and consumables taxonomy override positive machine parents, including the observed Plasma Accessories descendant. Generic Welding/Cutting types and slash tags on other origins remain insufficient.

The regression fixture retains six observed merchant records: both deep ESAB candidates, a stick welder, an engine-drive welder/generator, a plasma cutter and the actual plasma interface cable. Thirty-eight focused cases cover the observed positive types/tags, exact origin/path boundary, insufficient metadata, conditions/components/negative descendants, included torch semantics, no inferred kit/platform, full parser/normalization/query fact preservation, percentage ordering and unknown-stock exclusion. The contract is mirrored in project guidance and Trellis specification.

## Controlled replay

`research/classifier-replay.json` records an offline comparison against the committed classifier. All 197 parsed discounted IOC products were previously rejected. The candidate normalizes 195; the refurbished Lincoln welder and plasma interface cable remain excluded. Every parsed Product and each admitted exact offer field remains unchanged. This is classification evidence, not admitted inventory or a current merchant-stock claim.

The two retained earlier public source captures also remain identical: Max Warehouse's 38 normalized products and Fasteners Inc's 78 normalized products preserve all fields compared with the committed classifier. These older response bodies retain their original observation times in their own receipts and do not establish the current full public catalog state.

Classifier SHA-256: `1bb39fd0a39adbee451fa243aeda3d298bb7afcb7d4e30ee18cbe775d06eac73`.

## Verification

- Full safe offline suite: **1559 passed**, eight existing warnings.
- Focused IOC regressions: **38 passed**.
- Exact repository CI Ruff scope plus the new IOC test: passed.
- Shared catalog JavaScript syntax, changed Python AST/JSON syntax and whitespace checks: passed.
- No type checker is configured.

No source was activated, and no commit, push, network request, database read/mutation or publication was performed by this implementer. The parent owns fresh admission, selected purchase-page/shipping/reference/condition checks, independent final review and any production rollout. The scheduled public tools snapshot advanced independently, so an older capture replay must not substitute for the parent's current baseline verification.


## Made-to-order correction — final implementation

The complete description review found six machine packages with positive Shopify availability and an explicit made-to-order shipment/lead-time range. The existing shared `availability.shipping_notice` dispatcher now recognizes the captured active IOC declarations in feed `body_html` and independently fetched product `description`. All affected variants retain the merchant notice and become unknown stock. Generic FAQ, service-parts, historical, hypothetical and inactive script/template text do not establish that notice. The other retailer decoders are unchanged.

`common/tests/fixtures/ioc_made_to_order.json` retains all six observed identities, variants, prices, taxonomy and exact active notices. Twenty-five stock regressions cover each notice, independent audit rejection of stock alone, source isolation, non-active text, explicitly unavailable variants, unchanged exact offers, query exclusion and earlier daily evidence. Together with the classification cases, the focused IOC suite passes **63 tests**.

`research/stock-replay.py` and its separate JSON receipt compare both complete retained collection bodies under committed versus candidate availability using the same candidate classifier. All **197 parsed discounted products / 195 normalized machines** reconcile: exactly **six** products change only offer availability and notice; every other parsed and normalized fact is identical. Historical capture-day stock-only results fall **195 → 189**; the two deep offers remain. No source timestamp is saved or renewed, and this historical replay is not fresh admission. The earlier classifier-only receipt remains untouched.

Final corrected-code verification: **1,584 passed**, eight existing warnings, through the safe offline check wrapper. Exact CI Ruff scope plus the changed decoder, new stock test and replay script passes; shared JavaScript syntax and whitespace checks pass. No type checker is configured. The availability module SHA-256 is `3872262ca5571d3a3f66c76f2a8184c0bc392108860569fffa0f322f15dbc0f6`; the classifier remains at the earlier hash. No additional runtime edits followed these checks.

Source activation, fresh endpoint checks/admission, final independent review and publication remain parent-owned. This implementation used retained public captures and temporary test/replay files only; no network, operational database, credentials, commit, push or deployment action occurred.
