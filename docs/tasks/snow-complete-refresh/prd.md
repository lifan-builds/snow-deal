# Do not renew incomplete snow sources

A failed or incomplete retailer refresh must not create newly dated deals or variant/history observations, even when the partial count is large and there is no previous baseline. Retain the last successful rows with their original age. Other complete sources may still publish when the existing minimum-source gates pass.

Observed production run 41948669174 returned Backcountry errors=1 and selector_missing on one collection, but withheld_stores=[] because the collapse guard only checked a 70% count drop. This contradicts the source completeness contract. Acceptance: partial sources excluded before persistence, explicit receipt reasons, truthful min-source gate, deterministic regressions for errors/noncomplete collection states/new sources/count collapse and successful sources. No historical timestamp repair or production DB mutation.
