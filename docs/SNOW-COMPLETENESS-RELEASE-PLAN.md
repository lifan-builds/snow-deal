# Snow source completeness correction

An incomplete retailer refresh can currently renew its returned offers whenever its count stays above the collapse threshold. Run 41948669174 exposed the problem: Backcountry reported selector_missing but was not withheld. This release withholds explicitly failed or incomplete sources before deal/history persistence, regardless of their count or whether a baseline exists. Complete sources still publish through the existing minimum-source gates.

Scope is the snow snapshot admission guard and regression tests. The House exact-variant adapter is a separate candidate and is not activated by this correction. No existing price/offer observations are rewritten, and this correction does not retroactively validate past observations.

Validation: scoped gate tests, meaningful temporary persistence regression, full offline suite, independent review and CI. After merge run a fresh snow refresh and verify the report, withheld-source ages when present and production snapshot timestamp. Roll back the code commit if complete sources regress; retain all previous source data and dated evidence. Publication is covered by the user's standing approval for comparable releases.

Status: PR #19 merged as `2f471fd`; CI `41966779145` and targeted refresh/deployment `41966876680` passed. The provider endpoint and runner custom-domain check serve the new snapshot. All unselected deal/offer/run rows and prior history remain unchanged. The [rollout receipt](benchmarks/2026-11-05-snow-completeness-rollout.json) records exact hashes, checks and limitations.
