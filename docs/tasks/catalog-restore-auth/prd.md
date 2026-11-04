# Preserve catalog history during GitHub API rate limits

Cycling job 126388372512 in run 41773486321 failed before refreshing because its unauthenticated GitHub release-metadata request returned HTTP 403 rate limit exceeded. The existing production snapshot remained intact.

Use the workflow's existing read-only GITHUB_TOKEN for the fixed api.github.com release-metadata request only. Keep asset/CDN requests unauthenticated and refuse metadata redirects. This uses GitHub's documented authenticated request allowance without changing permissions or retrying a blocked anonymous request. Public local restoration still works without a token.

Acceptance: normal history restoration succeeds; no token reaches an asset or redirected host; 302/403/429 metadata responses still fail without bootstrap or destination creation. No history, validation, merchant-audit or freshness gate is weakened.

Scope: restore script, the restore step's environment, and deterministic transport regressions. Existing publication permissions stay contents: read. Validation: 577 tests, exact CI Ruff and whitespace checks pass, with four existing warnings. Merge after green CI under standing approval, then run the normal refresh after the current tools job finishes; verify both exact hashes. Revert this commit for code rollback, preserving prior live snapshots.

Reference: [GitHub REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
