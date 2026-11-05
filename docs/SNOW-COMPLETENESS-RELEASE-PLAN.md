# Snow source completeness correction

An incomplete retailer refresh can currently renew its returned offers whenever its count stays above the collapse threshold. Run 41948669174 exposed the problem: Backcountry reported selector_missing but was not withheld. This release withholds explicitly failed or incomplete sources before deal/history persistence, regardless of their count or whether a baseline exists. Complete sources still publish through the existing minimum-source gates.

Scope is the snow snapshot admission guard and regression tests. The House exact-variant adapter is a separate candidate and is not activated by this correction. No existing price/offer observations are rewritten, and this correction does not retroactively validate past observations.

Validation: scoped gate tests, meaningful temporary persistence regression, full offline suite, independent review and CI. After merge run a fresh snow refresh and verify the report, withheld-source ages when present and production snapshot timestamp. Roll back the code commit if complete sources regress; retain all previous source data and dated evidence. Publication is covered by the user's standing approval for comparable releases.

Status: independent review passed; all 750 offline tests, exact CI lint, JavaScript syntax and compilation checks passed. Publication and production verification pending.
