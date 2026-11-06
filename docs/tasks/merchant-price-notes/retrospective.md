# Evidence explanation retrospective

## Root cause

Implicit assumption across pipeline layers: the earlier comparison showed a product missing from normalized discounted/in-stock results. We described that as absence from the raw collection without checking raw membership. Both the primary explanation and independent review accepted the same inference. Runtime filtering and inventory counts were correct; the causal explanation was wrong.

## Evidence correction

The retained 01:32 UTC capture contains BMC Fourstroke R 01 ONE 2026 with all four variants unavailable. Previously accepted Large variant47432877080821 became unavailable, so the existing stock rule excluded it independently of the generated-option change. The later 02:08 UTC capture no longer includes the product. These are different dated observations and must not be collapsed into one claim.

## Prevention

For every explained population delta, join exact product handle and variant ID to the dated raw input before attributing the cause. Distinguish missing raw membership, unavailable variants, absent/invalid markdown, catalog exclusion, incomplete source refresh, and current-query filtering. If raw evidence is unavailable, describe only the observed normalized-result change. The parser contract and Trellis mirror now require this check.

No stock-change time or dead-offer-removal speed is inferred from the interval between observations. Likewise, an older missing pricing note means none was recorded; it is not proof the merchant caveat was absent. The new history explanation makes that limitation explicit, and regression tests prevent copying current notes backward.

## Scope

Correct the previous receipt and documentation with exact captured evidence; preserve all original raw captures and deployed inventory. No speculative runtime refactor, extra telemetry or new service is needed. Future reviews should challenge causal prose as carefully as numerical receipt joins.
