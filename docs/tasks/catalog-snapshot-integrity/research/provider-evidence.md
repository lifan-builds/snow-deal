# Provider and observed failure

GitHub documents size and sha256 digest in release asset metadata: https://docs.github.com/en/rest/releases/assets#get-a-release-asset (read November 6 UTC).

Previous retained failure: .local/source-expansion/tools-precision-20261106/published-asset-verification.json. Canonical download initially returned the older 3,145,728-byte tools snapshot; current metadata described 3,239,936 bytes and SHA256 abf7a8f5f4971d1bfc9025cfb52933a30b8f45eb1de7a7fb2843982c12389a3b. The release verification caught it before deployment. Later canonical and provider copies matched. The exact intermediary/cache cause was not established.

A live fixed release API read at approximately 00:42 UTC exposed uploaded state, positive size and sha256 digest for both cycling.db (10,182,656 bytes) and tools.db (3,239,936 bytes). Do not weaken authentication boundaries to fetch metadata-supplied URLs, or treat download failure as bootstrap authorization.
