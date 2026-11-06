# Implementation status

Initial boundary: extend only the existing manually requested read-only candidate
admission. Keep the boolean opt-in and RA Cycles default/artifact; add a fixed
Grizzly choice routed through an environment-bound quoted shell case. Manifest
paths and artifact names are code literals, never arbitrary dispatch input.

Owned files initially: `.github/workflows/catalog-check.yml` and this status.
Root owns captures, runner dispatch, source/merchant admission and publication.
Classifier/source activation is outside the current implementation assignment.
Circle untracked files, PLANS and other agents' changes remain untouched.

No network, permission changes, deployment, source activation, commit or push.
Workflow implementation is stable and root has been notified.

## Workflow changes

- Preserve `candidate_admission` as a boolean defaulting to false. Add
  `candidate_source` as a choice with `ra-cycles` default and `grizzly` as the
  only additional value. A legacy dispatch without a choice retains RA behavior.
- Pass only the choice through `CANDIDATE_SOURCE` environment data. A quoted
  shell case chooses fixed versioned manifest paths and fixed artifact names;
  unrecognized values exit before running Python or writing an artifact output.
  No expression or arbitrary user path is inserted into shell source.
- Both candidates use the unchanged probe command, 30-page cap, isolated
  `$RUNNER_TEMP/source-admission` directory and merchant audit. The existing
  45-minute job timeout and candidate/audit policies are unchanged.
- RA retains `ra-source-admission`; Grizzly uses `grizzly-source-admission`.
  Write the fixed artifact output before probing so a valid candidate failure
  can still upload its failure receipt. An invalid choice has no artifact output.
- Preserve manual-event plus boolean guards, repository `contents: read`, and
  the independently requested snow-preview job/gate. Candidate admission cannot
  activate a source, update public snapshots or trigger deployment.

## Verification

- Parsed the workflow through installed Ruby YAML/Psych and checked the boolean,
  default choice and read-only permissions.
- `bash -n` passed for the actual extracted candidate step.
- Executed that same shell with a temporary stub `python`, confirming exact
  manifest/CLI arguments and artifact names for both RA and Grizzly. Four unknown,
  path and shell-expression choices exited1 without executing the stub, writing
  artifact output or creating shell-expression side effects. No network.
- Both referenced manifests parse as nonempty JSON candidate lists.
- `git diff --check` passed. No configuration-mirroring test file or dependency
  install was added. actionlint/shellcheck are unavailable locally; actual GitHub
  workflow validation/admission remains part of root's runner check.

## Remaining handoff

The implementer changed only the workflow and this status. Root owns review,
publication/dispatch, the actual production-runner access result and merchant
admission. Local access/audit evidence cannot establish runner access. A runner
403/429, incomplete traversal or mismatched/inconclusive audit keeps Grizzly
excluded. Classifier changes for rejected machines remain deferred until root
completes its primary-product evidence and explicitly delegates that scope.
