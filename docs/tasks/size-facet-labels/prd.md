# One menu entry per existing size match

Status: released and verified (PR #26); authorized under the user's standing instruction to improve catalog UI/data quality and publish comparable verified releases.

Big Ring's live frame-size menu repeats labels such as M, MD, MEDIUM and Medium even though the existing exact-size matcher treats them equivalently. This makes choosing a fit harder without offering a different result. Show one deterministic menu entry for each existing size_key equivalence group. Preserve the exact selected merchant size, price, reference, stock, options and URL on cards/history. Old URLs and saved searches must continue selecting the same population and show the matching menu option selected.

Do not expand size equivalence, infer fit, merge compound labels, change ranking/counts/pagination, rewrite snapshots or histories, change brands, add sources or redesign the page. Only currently in-stock labels in fresh sources supply facets, as before. Unknown requested sizes remain selected and yield the existing empty result. Tools' optional generic size facet uses the same shared behavior without merging model identifiers. Fresh Powder's separate web app is not changed.

Acceptance: duplicate normalized keys disappear; source iteration order does not alter labels; legacy aliases retain selected form state; compound/numeric-s sizes remain distinct; identical snapshot/filter inputs return byte-for-byte equivalent selected cards/order/counts; existing complete offline suite passes; deployed pages show the simplified menu with unchanged data fingerprints.
