# Catalog release receipt — 2026-11-03 UTC

The approved release is live at [Fresh Powder](https://freshpowder.clifan.com), [Big Ring](https://bigring.clifan.com), and [Bench Drop](https://benchdrop.clifan.com). This receipt supersedes the prepublication status in the release plan; its earlier inventory counts remain historical observations.

## Automated publication

- Production main: `0530cad027b1f2189ec327b2160e70d503b48ec1`, including approved release PR #4 and recovery PRs #5–6.
- [Catalog refresh 41580573050](https://github.com/lifan-builds/snow-deal/actions/runs/41580573050): both jobs succeeded, including merchant audits, deployment and exact live snapshot verification. Existing history was restored (`bootstrap_history=false`).
- [Snow refresh 41576089057](https://github.com/lifan-builds/snow-deal/actions/runs/41576089057): succeeded; production verified snapshot `2026-11-03T04:49:46.141708`.
- Eight-hour schedules are enabled: cycling/tools at 00:43, 08:43, 16:43 UTC; snow at 05:17, 13:17, 21:17 UTC. Successful manual dispatch verifies the workflow; future scheduled executions still require monitoring.

## Verified live inventory

| Measure | Big Ring | Bench Drop |
|---|---:|---:|
| Fresh configured sources | 16/16 | 8/8 |
| Eligible in-stock listings | 1,141 | 548 |
| At least 40% off, above reference floor | 87 | 19 |
| Retailers contributing a qualifying deep deal | 11 | 3 |
| Fresh merchant audit matches | 30/30 | 30/30 |

Reference floors are $1,000 for cycling and $200 for tools. Listing counts are not unique model counts. Audits sample the top ten plus twenty seeded offers against merchant product endpoints; they do not establish 99% population accuracy, checkout availability, or independently verified historical selling prices.

Live health matched the packaged SHA-256 at 05:00 UTC:

- Cycling: `0762426157018d62aec91eb01435b9d4ece1f60f347b5ef4f535124f21b6c3bb`
- Tools: `1e60b7351ff4964a570a633ea3e9e25577d8a2b9824e51bd9eaba4c187856c82`

Default and filtered pages passed descending-discount, exact variant destination, budget and reported-stock checks. Cycling medium-size and tools kit filters, history links and source pages passed. Bench Drop displays the Grizzly exclusion notice.

Snow reports 13,483 listings, 27,001 variant offers and 8,187 confirmed-size deals across 30 stores with deals. This is not complete coverage: MEC returned HTTP 403 and five Ski Essentials collections stopped at pagination errors. A browser observation showed the Ski Essentials newsletter overlay blocking Show More; after dismissal, products increased from 48 to 96 to 144. A scraper correction remains pending validation.

## Deployment credential recovery

The Gmail connector's saved OAuth authorization was rejected with `invalid_grant` before mailbox search. The provider did not establish the specific expiration or revocation reason. Added a safe reconnect command and actionable sanitized error reporting; 90 focused tests passed. Reconnected the existing read-only source and verified a recipient-scoped code request through a fresh authenticated broker. Previously running broker processes retained old connector state and were not all restarted because they also serve other chats.

The repository's `VERCEL_TOKEN` was updated at `2026-11-03T04:51:44Z`. Successful automated production deployments above prove the replacement credential works. No token or email code belongs in this receipt.

## Remaining work

- Taylor, Fasteners and Gravity additions are integrated locally at `c5f0bfd` with 454 passing offline tests, but remain unpublished. Fresh combined admission audits and release review are still required.
- Grizzly and MEC remain coverage gaps. Ski Essentials pagination needs the narrowly scoped overlay fix and live validation.
- Thirty real daily observations and broad competitor measurements are not yet available. This release does not establish leadership on all ten metrics.

Local public evidence is retained in the release worktree under `.local/release/fourth-run/`, `fourth-run.log`, `snow-full-refresh/`, `live-smoke.json`, and `skiessentials-pagination-observation.json`. These local artifacts are not committed or needed by the deployed application.
