# Implementation status

Boundary: correct Circle's inner quoted option-list decoding and the explicitly
proved numeric-inch hidden-label omission in the task-owned `implementation-tree`.
Valid outer JSON remains strict JSON. Preserve exact output option values,
variant identities, money, stock, images, selected HTML/API agreement and all
existing completeness checks. No main-checkout runtime/test edits, network,
source activation, budget change, database, commit or deployment.

The factual pair `profile/responses/0226.gz` + `0227.gz` exposes two independent
facts: the endpoint's valid CSV title and native selected/dropdown values retain
inch quotes (`22"` through `30"`), but the hidden variant DOM literally reports
`Size: 22` through `Size: 30` without those quotes. Correct CSV decoding must not
silently erase that conflict. Root subsequently verified native 23-inch and
24-inch selection reaches the exact corresponding API/form IDs, then explicitly
scoped the narrow comparison rule in design.md. Kader's captured pair0352/0353
has the same evidenced shape.

## Implemented isolated checkpoint

Only `common/deal_common/parsers/thecircle.py` changes runtime behavior. It uses
strict stdlib CSV for the quoted inner list while retaining unquoted single
labels and duplicate-dimension checks. Native choices are read from the existing
size select. A numeric API size matching `[1-9][0-9]*"` may compare with the exact
hidden numeric label only when its quoted native value occurs once, no native
unquoted alternative exists and the full compared option tuples do not collide
across variant IDs. All other options and evidence remain literal checks; output
retains exact quoted API values. No sold-out identity or no-option fallback added.

The eight root-applicable files are:

- `common/deal_common/parsers/thecircle.py`
- `common/tests/test_thecircle_options.py`
- `common/tests/fixtures/thecircle/chino-inch.html`
- `common/tests/fixtures/thecircle/chino-inch.json`
- `common/tests/fixtures/thecircle/kader-inch.html`
- `common/tests/fixtures/thecircle/kader-inch.json`
- `docs/project-guidance/aggregator-data-and-parsers.md`
- `.trellis/spec/deal/aggregator-data-and-parsers.md`

Both reduced fixtures retain functional public identity/options/money/stock/image
facts, omitting unrelated scripts and descriptions. The 45 new cases cover valid
CSV, malformed fields, original unquoted/quoted shapes, literal embedded commas
and doubled quotes, both authentic inch families, exact offers, duplicate/native
unquoted choices, full tuple collisions, wrong dimensions/numbers, nonnumeric or
other quote/unit forms, unavailable siblings and selected-ID substitution.

## Checks and replay

- First focused regression run against unchanged main code: **6 failed,
  22 passed**, reproducing the inner JSON/CSV defect and literal inch handling.
- Current focused Circle checks: **138 passed** (93 existing, 45 new).
- Full isolated `python scripts/check.py -q`: **1,298 passed**, eight existing
  warnings, in 6.60 seconds.
- Exact catalog CI Ruff scope plus Circle parser/new test: **passed**.
- Existing catalog JavaScript syntax check: **passed**.
- `git apply --check` for the scoped patch and main `git diff --check`: **passed**.

Local replay artifacts live inside the isolated tree at
`.local/circle-completeness/`: `replay.py`, three frozen request lists,
`replay.json` and root-applicable `changes.patch`. The frozen lists contain715
current profile requests,176 prior candidate requests and61 additional captures;
each retained body was SHA-256 checked against its original metadata and retains
its original URL/time. No requests or old captures were changed.

Across447 available HTML/AJAX pairs,445 prior passes retain every Product/offer
field exactly; only Chino and Kader newly pass (12 correctly decoded variant
labels). There are no paired regressions, remaining paired parse failures or
unsupported API option formats in this freeze. This is a replay checkpoint, not
complete-source admission: five HTML captures lack a paired API response and one
historical additional-capture HTTP404 is retained. Three unpaired HTMLs fail the
existing button identity check (shirt, Coast Hoodie, Skate Loose Chinos); Pink
Sequin Bow Bag fails the existing option-label check; Raglan Tee was still in
flight and its HTML resolves a normal evidence URL. These remain explicit.

Main parser SHA-256 remains
`158247ca9e4ef7163bee8fae9867780603100ace4a59cfc113d3a907df829504`.
This isolated checkpoint SHA-256 is
`f499b799802cae6a8fe67d04b1b67bc306bde5933e9cf3d81136b04aa2c60546`.

## CSV/inch review completed; separately authorized structural work

The reviewer corrected stdlib CSV's acceptance of bare quotes in unquoted fields,
preserving valid mixed CSV and unquoted single labels. Eight additional cases
cover this independently on selected, available and unavailable variants. Final
CSV checkpoint: **146 focused /1,306 full tests pass**, exact CI/extra Ruff,
JavaScript/Python syntax and whitespace checks pass. The same447-pair frozen
replay passes with unchanged445 prior results and only the two new inch families.
Its final parser hash is
`d5cc525868f5a83e380cc934892ca6aa2bdf386a4b936ec0db4c5e42cef9267b`.
Code/contracts/patch/replay were preserved in the isolated local
`csv-inch-checkpoint` directory before further edits.

Root completed the main diagnostic and supplemental public captures, updated the
design/implementation plan and authorized the next isolated scope after reviewer
release. Required form-scoped quantity IDs will establish HTML PID on every page;
present button IDs must agree, and absent purchase identity requires the exact
OutOfStock panel/control plus independent unavailable tracked-zero selected API
evidence. Existing reduced fixtures' omitted quantity inputs will be restored
from retained real originals. A coherent one-ID native/API/hidden Default shape
will produce sizeNone and empty options, preserving money/stock/images/identity.
No generic identity fallback or One Size inference is authorized. Factual pairs
and adversarial regressions, complete offline replay/full checks and a further
independent review are required. Main runtime remains unchanged; root owns final
admission, activation and publication.

## Structural checkpoint complete

The isolated parser now requires one real form-scoped quantity identity on all
pages and checks present/partial button identity against it. Missing button
identity requires the exact captured OutOfStock panel/control and an independently
unavailable/not-on-stock/tracked/zero/no-backorders/no-delay selected API tuple.
Every sibling is still reconciled. The singleton Default branch requires exact
native ID/label/displayed price, no other selectors, literal hidden Default
labels, one API Default/default=true record and empty top-level variant. Output
retains sizeNone and empty options; no One Size or stock inference.

Quantity inputs in14 earlier reduced fixtures were restored from retained actual
HTML, with local per-file provenance. Thirteen additional reduced factual pairs
cover nine selected-sold-out families, the Default bag, two exact native inch
selections and the active Black L shirt selection. The new structural module
adds55 cases: **18 failed/37 passed before**, then all201 Circle tests passed.
Full isolated suite: **1,361 passed**, eight existing warnings. Scoped Circle
Ruff passes; mirrored contracts retain the reviewed CSV grammar correction.

Root's unchanged production fetcher, using MockTransport only, completes both
18-page collections and all405HTML/405API families with zero errors, producing405
Products and1,042offers. Receipt:
`implementation-tree/.local/circle-completeness/production-structure-v1/report.json`.
All original capture times are retained; this is offline replay, not freshness
or merchant admission. A separate518-pair retained replay preserves all504 prior
passes exactly and recovers the12 affected families plus two exact inch selection
URLs. No current unpaired evidence/format failures/regressions remain in that
snapshot. One older additional-capture404 is retained as historical evidence.

Structural parser SHA:
`c68199e014729ee00d97e331c86d4f651efa3fc8a14f86d0cfc7b05074b7d19b`.
The local `structure-checkpoint` preserves its code/contracts/48-file patch before
further changes. Main parser still has its original158247ca hash. Independent
structural review is in progress; root's fresh capture uses a separate immutable
copy of this checkpoint, so subsequent metadata work cannot mix parser provenance.

## Authorized next boundary: factual child-sizing metadata

After the successful structural replay checkpoint, root approved Circle-only
Product.product_type metadata `Includes children sizing` from exact bounded age
labels (observed years≤16/months≤24/toddler codes≤10, ordered ranges and narrow
observed wrappers), the captured bounded child-age description, or exact Miles
brand identity plus chart-supported numeric2–14 labels. All405families/full raw
variant sets are reviewed; unknown/adult/contrary sizes stay uninterpreted and
every offer remains intact. This marker states containment rather than asserting
all siblings are children. Existing snow whole-family exclusion consumes it;
no categorizer/source activation changes are owned here. Adult/bad-bound and mixed
family controls, exact all-offer replay and another full review remain required.

## Age metadata checkpoint recovered and verified

The isolated age change is complete: all275 Circle tests pass, including74 new
age/consumer controls. The complete isolated safe suite passes1,435 tests with
eight existing warnings. Exact existing CI Ruff plus Circle parser/tests,
JavaScript syntax and affected Python compilation pass. Two mechanical age-scope
Ruff findings were corrected after the original replay processes terminated
(`re.I` alias and import formatting); focused tests and final-hash replays pass.

At parser checkpoint
`c8483d27b4248d91ffd3e949175dbc52d6ad7228c251b2a7821e50a1dd8e3778`,
the unchanged production fetcher completes405HTML/405API families across36pages
with zero errors and1,042offers. The final retained replay covers518 pairs,
preserves all504 prior supported pairs' offer/non-metadata facts exactly, and
has no format failures, regressions or unpaired responses. The historical Rodan
404 remains explicitly retained. See isolated local `production-final/` and
`retained-final/` receipts. No observation timestamp was refreshed by replay.

A complete structural-versus-age comparison proves that all405 Products retain
every field except optional product_type, and all1,042 offers remain exact.
Seventy-nine families gain factual containment metadata:65 explicit bounded
age-size sets,12 exact Miles identities/chart-supported numeric-size sets and
two explicit bounded child-age descriptions. Existing snow conversion changes
144 accepted rows to115, withholding29 previously exposed child families and
adding no products. Every changed full variant set and all62 remaining
apparel/accessory rows were reviewed in the isolated local
`age-reconciliation/report.json`. No remaining row has the scoped explicit age
or exact Miles evidence. Unknown sizes remain unknown; this review does not
prove all unlabelled sizes adult or establish casual/skate clothing as snow gear.
Six uncategorized rows and existing generic casual-apparel classification remain
root-owned admission considerations.

Historical checkpoint, superseded by the root integration checkpoint below:
the independent reviewer reproduced a separate present-purchase-button
contradiction and owned its narrow control validation/real-fixture restoration
follow-up. Parser/tests/fixtures ownership was released after both final-hash
replays terminated; implementation holds those files pending reviewer completion.
The root-applicable final patch must be regenerated after that correction.
Main parser/test bytes, source configuration/activation, databases, history and
frozen fresh-capture parser remain unchanged by this implementation work.

## Root integration checkpoint

The reviewed 63-file patch (SHA256 `60016ad0e2ab790ecdce46ca6d5acd82b34f5b16fdba5b34f7f72f845eaf0495`) is applied to `codex/circle-exact-offers-release`. The root parser now matches final reviewed SHA256 `08069d99db46af8aee4c467093bc02aa55ffe46ca041e5e365a0ef477f825014`. Original 93-case test file is unchanged. Source configuration remains inactive. The earlier full diagnostic is terminal; the later current recheck imports its separate immutable structural parser, so applying root code cannot change its captured inputs or results. Current raw bodies still require a final-parser replay and independent selected-offer audit before activation.
