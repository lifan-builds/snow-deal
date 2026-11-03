# Variant shipping evidence follow-up

Local follow-up to prepared release `35f2bfb`, on `codex/variant-shipping-evidence`. Not published. The earlier publication approval request remains scoped to `35f2bfb`; this follow-up is separate.

## Observed problem and correction

Harvey's GYRO AIR G-700Pro lists both colors as orderable, but the vendor field and public page disclose an estimated November 30 shipment for Black. Treating `available: true` as confirmed stock hid this conflict.

The shared Shopify parser now preserves Harvey's shipping notice on the affected exact variant and marks its stock unknown. Unambiguous color metadata preserves the white variant's separate status. The default ranking still prioritizes percentage discount; stock-only filtering excludes delayed variants before selection. Cards and variant history show the notice. An independent product-endpoint audit rejects an in-stock claim when the same notice contradicts it.

This is a source-specific interpretation of observed evidence, not a general promise that orderable Shopify products are physically stocked. Shipping dates are not inferred or automatically expired. No checkout, delivery-date or historical-selling-price validation is claimed.

## Verification

- 501 offline tests pass, including parser ambiguity, host scope, stock filtering, independent audit, persistence and rendering regressions.
- CI's Ruff scope plus the new parser helper and regression file pass.
- A fresh production-path Harvey refresh completed: 18 discounted products parsed, 11 accepted. Only Harvey was refreshed in a new copy of the task-owned public snapshot; other sources remained identical as decoded records.
- Exact product endpoint: white `47142200574170` matches identity, USD price, reference, options and reported stock. Black `47142200606938` matches all except confirmed stock, which the audit correctly rejects.
- Both variants remain $3,299 against a $3,999 retailer reference at the recorded observation. The default and stock-only views select white at equal discounts. A regression also covers a cheaper delayed black variant winning the unfiltered ranking while white wins stock-only.
- Harvey's confirmed-stock variants decrease from 14 to 13, with one unknown. The tools snapshot retains 607 eligible stock-only listings because white remains available for this product.
- Desktop and 390 × 844 browser checks show the notice and exact destination on variant history. Mobile document width equals viewport width (390 px). Temporary viewport overrides were cleared.

Public evidence: [fresh refresh and exact-variant audit](benchmarks/2026-11-03-shipping-evidence.json). The negative black audit is intentional regression evidence, not a passing production audit. Full release merchant samples and deployment validation remain required before any later publication.

Local preview and screenshots: `.local/shipping-evidence-20261103/`. Prepared `35f2bfb` snapshots were preserved. No source schedules, live data or deployments changed.
