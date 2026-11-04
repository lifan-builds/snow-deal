# Shipping evidence and Bike Closet release — 3 November 2026 UTC

Branch: `codex/bike-closet-source`. Base: approved release `9b421b7` (PR #7). The user has authorized comparable future releases for Fresh Powder, Big Ring and Bench Drop without another confirmation. This plan records the concrete follow-up scope; production success still requires evidence.

## Behavior

- Add Bike Closet to Big Ring: its corrected candidate has 19 qualifying deep listings from one additional useful retailer. Exact size/color/SKU links, explicit USD references and new-condition evidence are required. A conflicting SIZE L / XS listing is excluded. Delayed variants remain unknown and cannot satisfy exact-fit or stock-only requests. Preserve regional shipping restrictions, final-sale and frameset-photo notices.
- Harvey's explicit estimated-shipping notice overrides generic availability for affected variants. Show that notice on current cards and dated history. The affected black G-700Pro remains unknown while the white variant retains its separately established stock state.
- Preserve otherwise-identical variant history when an old fulfillment label is cleaned from the manufacturer field. True manufacturer/model/option changes still break identity. No historical dates, prices or stock are rewritten.
- Include the tested Rockler candidate decoder and bounded evidence transport. Rockler remains disabled because its full live admission was rate-limited. No Rockler offers are part of this release.

## Validation

546 offline tests and exact CI Ruff checks pass. Bike Closet's complete candidate traversed all 31 public category variable-product records and checked 26 equipment pages. All 19 final selected offers matched separate merchant reads; the long elapsed audit window prevents an M3 accuracy-score claim. The final candidate applies deterministic size and manufacturer corrections to the complete snapshot without advancing its observation timestamp. Local mobile review shows zero initial price scroll and readable unknown-stock notices. See the dated Bike Closet, shipping and Rockler receipts for limitations.

## Rollout and recovery

1. Wait for the approved PR #7 rollout to finish and record its actual result; do not confuse a merge or preview with a fresh production snapshot.
2. Push this branch, require green PR checks, then merge under standing authorization.
3. Run the existing catalog refresh with `bootstrap_history=false` and the full snow refresh. Restore public history; require complete configured sources, passing merchant audits and exact live hashes. A blocked merchant remains a real release failure; do not lower checks to publish it.
4. Verify production Bike Closet filtering, precise purchase links, shipping notices, price ordering and history. Record actual counts and timestamps, not the local candidate numbers as if they were production.

If a catalog fails its release checks, retain its existing live deployment. For a deployed regression, restore `9b421b7` with a fresh validated snapshot and preserved history. Never relabel an old snapshot as fresh. No additional paid service, account, DNS or credential changes are required. Thirty days of real history and all-competitor metric leadership remain unproven.
