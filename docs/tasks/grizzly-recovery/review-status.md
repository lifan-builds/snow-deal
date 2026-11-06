# Independent workflow admission review

The standalone workflow/manifest change is ready for publication and actual runner validation. No defect was found and no workflow correction was necessary. This review does not admit Grizzly or approve a classifier/source change.

The existing boolean opt-in remains false by default. The new choice defaults to RA Cycles, with Grizzly as the only additional allowlisted value; the explicit fallback preserves legacy dispatches. A quoted shell case maps environment data to fixed tracked manifest paths and fixed artifact names. No dispatch value becomes shell source, a manifest path or artifact text. Invalid choices fail before Python execution or output creation.

Manual-event and boolean guards prevent candidate requests on pull requests or ordinary checks. Repository permissions remain `contents: read`; the offline/candidate job receives no service secrets and cannot deploy or update public data. The separately requested snow-preview job, its false default and its existing preview-only guards are exactly unchanged. Choosing a candidate does not enable that job.

Allowed choices write their fixed artifact output before invoking the unchanged bounded probe. A failed probe therefore keeps its nonzero status while the always-upload step can preserve any isolated failure receipts. Earlier skipped/failed checks or an invalid choice cannot accidentally select an artifact name. RA retains `ra-source-admission`; Grizzly uses `grizzly-source-admission`, with the same output directory and thirty-day retention. Both manifests parse and bind the intended public retailer; the Grizzly manifest uses the existing exact-SKU parser and canonical host.

Independent offline verification passed:

- Ruby/Psych YAML parsing and `bash -n` on the actual extracted candidate step.
- Exact argument/artifact checks for both allowed choices, including nonzero probe returns.
- Four unknown/path/shell-expression/newline inputs rejected without Python execution, artifact output or injection side effects.
- Read-only permissions, unchanged RA/snow behavior, manifest parsing and whitespace checks.

No workflow type checker applies; actionlint/shellcheck are unavailable locally. Root's shared offline suite and exact CI lint/JavaScript checks already pass; no Python runtime change justified repeating them. GitHub workflow validation and complete runner admission remain required. Local success cannot establish recovery from the prior runner HTTP 403, and any 403/429, incomplete source or failed merchant check keeps Grizzly excluded.

Only this review note was written. No network, credentials, operational databases, classifier/config activation, commit, push or deployment occurred. Circle work and root planning/research files were preserved.

## Final runner-result documentation review

The initial workflow readiness above preceded the actual runner check. Run42133246412 at `be7b5416e9687d045109fdaaa073549d6540507a` then failed on the first Grizzly collection request with HTTP 403. Its source is incomplete, zero pages completed and the merchant audit did not start. Both staged JSON receipts exactly match the original downloaded failure artifact, and the retained step log confirms the first-page 403. Zero sampled offers is not an accuracy result; Grizzly remains excluded and no classifier or inventory gain is claimed.

The staged planning/status and runner-result text distinguish passing code checks from failed source admission. The Competitive Benchmark paragraph agrees with the already-published Incycle receipt: 1,477 qualifying listings, 203 deep offers, seventeen useful retailers and a fixed thirty-offer sample plus84 targeted checks. Only documentation is staged; runtime/workflow and inactive Circle work are untouched. Artifact consistency, scoped credential-signature and whitespace checks pass. No remaining documentation blocker was found; no runtime test rerun or network action was needed.
