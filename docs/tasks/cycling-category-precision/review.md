# Independent cycling category review

Reviewed the complete cycling classifier/test diff, PRD/design, existing shipping/condition/accessory contracts, retained raw/public replay and separate purchase-page category evidence. The positive frame taxonomy uses full matching and runs after existing negative gates. A complete bike describing carbon frame material stays a complete bike. Primary apparel cannot become equipment through generic Bike taxonomy; explicitly included apparel does not replace the primary bike. No brand/model exceptions, fit inference, transport, ranking, source, stock or history-policy change was introduced.

## Fixed and strengthened

The primary-title split required whitespace after w/, causing `Road Bike w/Gloves` to be newly rejected. Changed only the included-suffix delimiter to allow compact w/ wording while keeping the preceding whitespace boundary and the existing with/including word boundaries. The positive regression failed before the fix; `Bike Gloves w/Road Bike` remains rejected. All full-title condition and negative taxonomy gates remain intact.

Added an end-to-end normalization/query regression: an explicit Mountain Frame becomes Framesets, a complete Mountain Bike with Carbon Frame remains Mountain bikes, and the glove is absent even with a zero reference floor. It checks raw input immutability, exact selected variant/options/size/price/reference/URL, category-filtered count and exclusion of an unknown-stock size.

## Retained evidence reviewed

The retained Gravity feed has 397 raw products: three classifier removals, of which only the Thrillium glove is discounted. The rental package's helmet wording also causes a raw removal; this is a literal title match, not a new semantic rental policy. PBS has 594 raw products: 35 additions and three category changes; the discounted subset has fourteen additions and one change to Framesets. These are dated feed replays, not fresh stock admissions.

Both retained public snapshots contain 1,512 product records. Their reconstructable-field replay shows only the intended glove removal and Mondraker category change; missing original tags prevent treating that replay as a complete new ingestion audit. Separate canonical/title/specification evidence supports all fifteen changed discounted PBS listings. Two FOXY paths share SKU010.25US086, so these remain merchant listing counts rather than unique models or distinct inventory claims.

Compared the candidate-loaded and final compact-w/ classifiers on every retained raw product, including full-price and rejected products: zero differences across all 991 records. The exact reviewer receipt is review-compact-wslash-replay.json. Different raw inputs from the ongoing fresh all-source candidate must still be reconciled against the final classifier before publication; changed eligibility would require affected-source refresh/audit.

## Verification and remaining gates

The final full offline suite passes **856 tests**, eight existing warning emissions. The exact existing CI Ruff command passes. The cycling test file retains four pre-existing lint findings with zero added diagnostics; unrelated import/regex style was preserved. Changed Python parses and whitespace checks pass. No type-checker is configured.

No network, operational database, credential, commit or publication action occurred during review. The main session owns complete-source admission, the timed standard-plus-changed-listing merchant audit, prior-history checks, CI and deployed-snapshot verification. The code is stable; the source admission/rollout remains separate. No all-metric leadership or fresh merchant-accuracy claim follows from the retained research.
