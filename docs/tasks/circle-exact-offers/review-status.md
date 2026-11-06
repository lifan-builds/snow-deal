# Independent Circle exact-offer review

Code review passes after the local corrections below. The parser remains inactive: registry, source configuration, transport and request budgets are unchanged. Complete fresh source replay and independent merchant admission remain root-owned gates.

## Findings fixed

1. A conflicting or malformed `allow_outofstock_sale` could be ignored when `allow_backorders` was present, allowing contradictory evidence to confirm stock. Validate both supplied aliases and reject contradictions before using the existing stock logic. Three regressions failed before the correction.
2. A captured full 24-card first collection page with its pager removed became an apparently complete singleton. Full first pages now require pagination; the evidenced shorter singleton/full-price shape remains supported. The new regression failed before the correction.
3. An empty or whitespace-only HTML purchase heading could agree with an empty AJAX title and emit an unnamed product. Require a nonempty main title; collection-specific display aliases remain allowed. Both regressions failed before the correction.
4. The failed live candidate exposed unavailable full-price siblings with explicit `false` reference fields. Decode only that consistent absent-reference shape as zero reference; all supplied `price_old` fields must be false. Missing, malformed or conflicting money still fails. A newly available full-price sibling cannot borrow the selected variant's discount. The reduced real rainboot fixture and this no-borrow control failed before the correction.
5. The same candidate exposed a Kelly snowboard with no variant images but an explicit product-gallery fallback. Validate that fallback ID and URL against both HTML and AJAX galleries while leaving each unknown variant image unset. Explicit variant-image mismatches and unbound fallback images still fail. The reduced real Kelly fixture failed before the correction.

The two new fixture pairs contain only relevant public purchase metadata, controls, variant facts and gallery images from candidate responses 0021/0022 and 0174/0175. They do not include descriptions, scripts, credentials or browser state. Together, the added controls demonstrate nine fail-before cases across the five findings, with further negative regressions preventing unsafe relaxations.

## Cross-layer review

Reviewed the complete parser, fixtures/tests, task PRD/design/implementation artifacts, primary research and applicable project contracts. The parser reuses the existing detail/evidence hooks without common code importing a catalog. Exact canonical host/path, family and variant IDs, selected form/button, CAD visible/structured/formatted money, variant options, stock and image evidence bind before offers are emitted. Every variant supplies its own current/reference and merchant destination. Unknown/backordered stock remains excluded from exact-size and stock-only queries; explicit unavailable variants are withheld. HTML/JSON variant sets reconcile before filtering.

Pagination validates active/requested pages, sequential safe next links, stable terminal pages, nonterminal card counts and unique discovery identities. The existing fetcher retains its 500-family detail budget, pacing, cross-collection deduplication and fail-closed outcomes. No variant count is silently truncated. Raw CAD amounts are not converted or treated as USD inventory, and percentage-first offer ranking is unchanged.

The former browser's numbered-link fallback can traverse the observed pagination. Neither its explicit-selector mismatch nor the observed three-page public snapshot establishes why earlier coverage was partial. The current full profile is discovery evidence rather than proof of eligible inventory or successful production admission.

## Verification and limits

- **93 focused tests passed**; full offline suite after the corrections: **1,045 passed**, eight existing warnings.
- Exact CI Ruff scope plus the new parser/tests, Python compilation, whitespace and scoped owned-file credential-signature checks: **passed**. No type checker is configured.
- Independently replayed all **36 retained collection pages**: sale 413 and snow 424 identities, **771 distinct families / 406 discounted families**. These are family/discovery counts, not eligible listings.
- All **80 retained HTML/AJAX pairs** now pass, reconciling **409 variant rows**. The original incomplete candidate and its failure evidence remain preserved.
- Final parser SHA256: `158247ca9e4ef7163bee8fae9867780603100ace4a59cfc113d3a907df829504`.

No unresolved code finding remains within the reviewed captured shapes. The remaining live captures, complete production-fetcher replay, separately timed selected-destination audit, source activation and history-preserving release have not been established by this review. Unsupported default/option-label shapes remain fail-closed until actual merchant evidence supports them. The three retained nondefault selected-page checks support those exact destinations, not every variant or checkout availability.

No network, credential access, operational database, source activation, commit, push or deployment occurred during review. Only the explicitly authorized public captures were read. No generic HTTP, registry, source, schema, history or budget change was made.
