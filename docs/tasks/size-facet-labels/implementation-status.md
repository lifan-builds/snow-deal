# Local implementation and review handoff — 5 November 2026 UTC

The shared catalog query now groups only size facet labels by the existing unchanged size_key. Each group uses the shortest existing label; case-folded and raw lexical ties make the choice deterministic regardless of source or offer order. The facet result retains its existing list-of-strings shape. Only the same fresh, in-stock offers that supplied facets before are considered.

After the unchanged query selects offers, the web context resolves an incoming size alias to that group's representative. Form selection, the active filter, the explanatory label and generated pagination links use that representative. A requested size without a current representative remains selected verbatim and keeps its existing empty result; escaping is preserved. No template change was needed.

Implementation changes are confined to common/deal_common/catalog/query.py, web.py and common/tests/test_catalog_runtime.py. No size_key aliases, compound interpretation, raw offers, ranking, snapshot/history data, source configuration or Fresh Powder app behavior changed. No network, credentials, commit, push or deployment actions were performed by the implementer.

## Verification

Three meaningful regressions failed before implementation: duplicate facet labels and the legacy alias form-state tests for cycling and tools. Eight new cases now pass, checking case/whitespace/known aliases, existing rather than invented representative labels, source/offer ordering, stale/future/unknown-stock membership, compound and numeric-s distinction, model identifiers, old and unknown form selection, escaped unknown input and normalized pagination links.

The query regression compares complete serialized selected cards for equivalent aliases across two pages, including every original raw offer field, and verifies counts, order, purchase identity and input immutability. HTTP tests compare rendered card fragments for canonical and legacy requests on both shared catalogs.

The focused runtime module passes 46 tests. The full offline suite passes 827 tests with eight existing warning emissions. Query/web Ruff checks pass; the runtime test module retains its ten pre-existing findings with zero added diagnostics. Changed Python compiles and scoped whitespace checks pass. No type checker is configured.

Root's separate read-only public snapshot replay is recorded in research/public-snapshot-replay.json: cycling has 164 original labels and 128 existing equivalence groups, while tools retains four labels. Across 166 cycling filters/497 pages and six tools filters/27 pages, root reports identical selected cards, counts, order/pagination and snapshot bytes. No live refresh or observation timestamp renewal was needed for that replay.

Independent review, publication and live fingerprint/route verification remain with root. Implementation code is stable for review; only this status note was written after handing code ownership to the reviewer.

## Independent review

Review added a configured-source/unknown-stock regression and confirmed legacy URL selection plus unchanged fixture database bytes. Final validation: 47 focused runtime cases and 828 full offline tests pass, with eight existing warnings and no new lint findings. No runtime code changed during review. See review.md.
