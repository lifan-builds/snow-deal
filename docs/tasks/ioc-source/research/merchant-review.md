# IOC merchant review — November 6, 2026 UTC

The current source candidate uses the public all-welders and plasma-cutters collections. The initial complete production-path probe parsed197 discounted products and accepted0; the taxonomy gap is separately implemented/reviewed. Retained raw feeds contain198 and78 records (some not discounted). Replay timestamps are not source observation/admission timestamps.

Two deep candidate purchase pages were independently fetched on November6 at21:00:37–40UTC. Captures and request/hash receipt are retained in `.local/source-expansion/ioc-20261106-raw/selected/`. Both pages bind their H1, enabled purchase form, selected variant ID and USD InStock JSON-LD to the expected listing. They display the same sale/reference pair as the feed:

- [ESAB Rebel EMP205ic (0558102553)](https://www.weldingsuppliesfromioc.com/products/esab-rebel-emp-205ic-ac-dc-multi-process-welder-0558102553?variant=46439776813343): variant46439776813343, SKU IESB20170015, $4,195 / $7,015.13. Page lists power source, MIG gun, electrode holder/ground leads, wired foot control, TIG torch/accessories and regulator; complete machine with included equipment.
- [ESAB Rustler EM280 PRO (0700401201)](https://www.weldingsuppliesfromioc.com/products/esab-rustler-em-280-pro-mig-welder-0700401201?variant=49581664534815): variant49581664534815, SKU IESB20240029, $3,329 / $5,751.01. Includes power source/cord, MIG gun, ground lead, regulator and drive rolls. Optional spool gun is explicitly sold separately; it is not part of the selected package.

Prices are direct listed prices; reference values are retailer compare-at amounts, not verified historical selling prices. No rebate, free gift or financing amount is added to savings. These observations do not validate checkout, delivery timing or historical street prices.

[IOC's FAQ](https://www.weldingsuppliesfromioc.com/pages/help-faq) states economy shipping above $75 to the continental US, with liftgate and expedited services extra and other US regions priced separately. A generic warning that stock mistakes can lead to backorders does not identify either selected machine as backordered. Do not claim free delivery to every location. [The refund policy](https://www.weldingsuppliesfromioc.com/policies/refund-policy) includes machine restocking and shipping charges; product JSON-LD's FreeReturn marker is insufficient to advertise free returns. Cancellation text contains inconsistent fee references; no unconditional return/cancellation claim is appropriate. [About Us](https://www.weldingsuppliesfromioc.com/pages/about-us) identifies Indiana Oxygen as the parent and Indianapolis addresses.

The fresh admission remains a separate fixed top-ten/seeded-twenty plus all-deep audit. Product-page research is corroboration, not substitution for that timed gate. Source is inactive until review/admission succeeds. Complete description review then found six active made-to-order notices despite available=true. See independent-notice-review.json and made-to-order-page.json; the original30/30 sample is retained but not sufficient for admission. A shared source-bound shipping decoder and fresh full admission are required.

## Concurrent operational check

All three /healthz endpoints returned200: Fresh Powder ok/30 stores, Big Ring ready21/21, Bench Drop ready13/13. Current pre-release tools fingerprint is0a341fdfa2db0a3f63f3869378abfbb17cd4f6eef1418a613d45efd6daf2c9d8; Big Ring fingerprint caf800e7ff1d12f56ae20d0dd2d18702acc131174e8e358337d617b4401b2ffd. Exact response saved under `.local/source-expansion/ioc-20261106-ops/health.json`.

Scheduled run42251161355 completed tools successfully; cycling failed closed on Bike Closet HTTP429 with26matches,0mismatches,4inconclusive. Its original artifact is preserved under `cycling-failure/` there. A failed-jobs-only rerun was requested after several hours' cooldown, retaining the quality gate and previous valid deployment.
