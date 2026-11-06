# Implementation status

Boundary: build an inactive source-specific static parser using the existing
product-page and single evidence hooks. Listing discovery binds numeric family
ID and canonical www URL while permitting collection-specific display titles;
authoritative HTML/AJAX binds each actual variant, CAD money, stock, options,
image and destination. No generic HTTP, registry, source activation or budget
change. The unchanged 500-detail budget stays with the shared fetcher.

The initial selector mismatch does not establish that the old browser stopped
after one page: its numbered-link fallback may continue. New strict traversal
will be verified independently; the demonstrated gap is exact offers/stock/images.

Expected files: new common/deal_common/parsers/thecircle.py, reduced public
fixtures/tests and this status. Root owns full raw profiles, independent source
admission/audits, compatibility/registry decisions, production and release docs.
No network, operational/private state, deployment, commit or push by implementer.

Initial implementation is stable for independent review. Root began its paced
isolated candidate after the runtime checkpoint. The parser has remained
unchanged since that checkpoint; subsequent edits were fixtures/tests/status.

## Implemented

`TheCircleParser` opts into the existing `requires_product_pages` and single
`get_product_evidence_url`/`parse_product_evidence` hooks. The existing static and
browser registries/configuration remain untouched, so this implementation is
inactive. Common code does not import snow-specific code.

Discovery scopes cards to `#ls-product-results`, validates every numeric family
ID and exact canonical www URL (including full-price cards), and emits discounted
families only. Collection-specific display titles are permitted; detail identity
binds family ID+URL, never a title fuzzy match or listing-wide price copied to
variants. Full-price entries consume no detail request. The existing fetcher
deduplicates families across collections and preserves its 500-detail budget.

Strict pagination validates the requested path against the active numeric page,
safe sequential next links, the advertised terminal page, 24-card nonterminal
pages, unique IDs/URLs within/across pages, and an explicitly disabled terminal
forward control. Stateful collection checks reject skipped/repeated pages and
changing terminal-page evidence. A genuine singleton/full-price first page can
have no pager. Missing/challenge content, unsafe links and exhausted existing
HTTP/page/detail budgets cannot report a complete source.

The exported `detail_data(html, page_url, evidence)` binds main HTML purchase
panel/canonical/title, selected cart-action and button IDs, selected option
controls, explicit CAD/visible/structured money and new condition to the separate
AJAX family, selected variant and complete DOM/API variant set. A requested ID
that resolves to the default variant raises rather than silently substituting.
The evidence URL preserves an explicit ID/quantity selection. Duplicate JSON
keys, missing siblings and contradictory identity/price/options/stock/images
fail closed; theme JavaScript is never executed.

Every offer uses its own variant price/reference, dimension labels, exact
merchant destination, image ID and tracked stock. Confirmed stock requires
explicit available/on_stock, tracked positive quantity, no backorders and no
delivery conflict. Explicitly unavailable siblings are withheld. Incomplete or
delayed evidence retains an unknown status and note, which cannot satisfy stock
or exact-size filters. Images bind through actual retailer image IDs; absent
variant images stay unknown rather than borrowing a different variant image.
Percentage remains primary, with cash savings breaking equal-percentage ties.

## Fixtures and checks

- `common/tests/fixtures/thecircle/`: reduced Jackson/Rodan plus eight additional
  observed product HTML/AJAX pairs, the two first collection pages and two
  terminal pages. Keep main panel/controls, factual prices/options/stock/URLs and
  image metadata only; no long descriptions, unrelated scripts or browser state.
- Observed shapes: quoted multidimension labels, unquoted Size/Color labels,
  color-only singleton, six snowboard variants, twenty boot variants and all
  twenty-one pants variants. The entire DOM/API set is reconciled before
  unavailable siblings are removed from purchasable offers.
- `common/tests/test_thecircle.py`: **73 passed**. Negative controls cover exact
  selected/default substitution; family/variant/canonical/title/SKU/options/
  currency/visible money/image/stock conflicts; unavailable siblings; malformed
  quantities/money/JSON; duplicate/missing variants; unsafe/ambiguous URLs;
  distinct sibling money/images; incomplete/backorder/delivery unknown states;
  genuine sold-out families; discovery repeats/terminal changes/missing pages;
  full-price suppression; cross-collection aliases; and the unchanged existing
  HTTP/page/detail failure hooks.
- Full offline `scripts/check.py -q`: **1025 passed** (952 baseline +73 new),
  eight existing deprecation/key-length warnings.
- Exact existing CI Ruff scope plus the new parser/tests: **passed**.
- `git diff --check`: **passed**.

Jackson's captured purchasable offer is XL / Matte Black,
variant100724076, CAD81.00 /269.99, with its bound image and `?id=100724076`
destination. The unavailable L variant100724075 never becomes a confirmed-stock
offer. These are retained-input facts, not new freshness or checkout assertions.

## Remaining handoff and limits

No no-option/default-label product shape was present in the ten captures; the
parser deliberately requires observed labeled matrix dimensions until primary
evidence establishes another shape. Real delayed/untracked stock was also not
observed; those conservative unknown-state controls are explicitly synthetic.
Root owns full live candidate outcomes, any additional observed shapes, separate
selected-URL AJAX/merchant audits, all-current/public-history replay, independent
review and activation/publication. Any runtime correction during that candidate
requires coordination and revalidation against its retained parser revision.

The implementer has not changed common HTTP, registries, source configuration,
currency policy, budgets, schema, history or other retailers, and has made no
network, operational/private-state, deployment, commit or push action. CAD source
recovery does not establish a USD inventory or historical street-price claim.

## Reviewed correction checkpoint

The independent review fixed five issues with regression controls: stock alias conflicts, absent pagination on a full first page, empty purchase titles, explicitly absent reference prices on full-price siblings, and valid product-gallery fallbacks with no variant-specific image. Final results:93focused /1045full tests pass. See `review-status.md` for details.

A later bounded public capture stopped when the previously observed Rodan helmet returnedHTTP404. A separate recheck with production request headers also returned404 at2026-11-05T23:12:01Z. Retained data can validate decoding, but cannot establish a fresh complete source. No source activation or publication occurred. Preserve `research/live-source-failure.json`; recheck collection/detail consistency before attempting admission again.
