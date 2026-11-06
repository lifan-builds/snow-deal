# Independent review — 6 November 2026 UTC

## Findings (fixed)

No runtime or test correction was necessary. Root clarified the task's earlier/current raw-tag counts and dated BMC explanation during review. I independently verified the correction: the 01:32 capture contains BMC Fourstroke R 01 ONE 2026 with all four variants unavailable, whereas the 02:08 capture lacks that raw product. My previous generated-options review had accepted the incorrect raw-absence explanation; the corrected earlier receipt/review records now distinguish normalized exclusion from raw membership.

## Findings (not fixed)

No introduced correctness issue found. Extended Shopify lint has the same four baseline findings (one TRY004 and three FURB167 source lines), with zero new findings; unrelated cleanup is outside scope. The eight full-suite warnings are existing warnings.

Publication, the final clean package, native desktop/mobile inspection and production rollout checks remain root-owned gates. Current audit evidence establishes merchant endpoint agreement, not completed checkout, historical selling prices, quote-only inventory or an additional competitive lead. The browser observation confirms the caveat and enabled purchase control for one exact ordinary variant, not checkout behavior for all tagged products.

## Cross-layer review

- Reviewed the complete six-file runtime path, all three affected test files, task/research artifacts and the mirrored parser/web contracts after the implementer's final handoff. No runtime source was changed by this review; unrelated Circle and root work were preserved.
- Appending `VariantOffer.price_note=''` preserves legacy construction. The decoder uses only exact Contender apex/www hosts and the exact tag in supported list/comma-separated-string forms. It returns fixed factual wording and leaves money, reference, availability, size, identity and destination untouched; the generated-option guard remains separate.
- The selected offer carries its own note through query results to the price and details. Jinja output is escaped. History reads each matching dated candidate's optional value with an empty legacy default; it never borrows today's or another variant's note or changes identity matching. Existing styles, schema and daily retention are retained. Tests verify selection/counts/order/pagination/fit, legacy snapshots, escaped current/historical notes and read-only database bytes.
- The independently fetched product.js payload is decoded separately. Either a current or stored nonempty note requires exact agreement, so omitted, changed and obsolete caveats fail while ordinary price/stock checks remain active. Both-empty legacy audits preserve their prior checks/result shape.

## Verification

- Independent safe offline suite: **1,253 passed**, eight existing warnings. This shared checkout includes 93 inactive Circle cases; the clean release tree remains a separate root gate. Exact CI Ruff scope plus offers/new/generated-option tests, JavaScript syntax, affected Python compilation and whitespace checks pass. No type checker is configured.
- Independently verified all three fresh capture SHA-256 hashes and replayed both raw JSON pages with HEAD and the final parser. There are 182 accepted products and 524 offers; all normalized fields except optional `price_note` match exactly. The current raw feed has 27 tagged products, all 27 accepted, yielding exactly 57 noted offers. The earlier 28-tag raw census and later 27-tag census are dated separately.
- Read-only checks of the explicit public task snapshots confirm all 20 other source rows remain exact. Observation count stays 59: 58 earlier-day/other-source rows remain byte-equivalent, only Contender's 01:32 same-day observation is replaced by the real 02:08 observation. Baseline historical offers have no note backfill.
- Independently reconstructed and joined the completed audit population: all 57 noted in-stock variants across 27 products plus the fixed top-ten/seeded-twenty sample, with zero overlap, produce 87 exact selected-offer dictionaries. All 87 match, with zero mismatch/inconclusive results; every note agreement and other factual check passes. The common window spans 02:11:42.490309–02:15:52.089610 UTC, 249.599301 seconds, within fifteen minutes. Default confirmed-stock/deep counts remain 1,475/203.
- The added parser/web contracts match implementation, including the rule to check raw membership and exact variant prices/stock before explaining a normalized disappearance. Research and earlier-receipt corrections preserve the observed timestamps and do not change prior inventory counts or deployed data.
- No network, credentials, operational database, commit, publication or deployment action was used for this review.

Code/tests/contracts and source/audit evidence review pass. All reviewer-owned edits are finished; remaining release and production verification gates are recorded above.
