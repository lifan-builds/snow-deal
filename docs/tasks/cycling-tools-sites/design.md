# Design boundary

Current shared code stops at retailer/feed/variant primitives; only snow has a site and durable snapshot. Add a small shared catalog runtime in common/deal_common/catalog/ that consumes an injected catalog definition. It owns ingestion orchestration, SQLite source snapshots and dated observations, eligible-variant selection, query/pagination, and FastAPI/Jinja/vanilla-JS browsing. Reuse Product, VariantOffer, ShopifyParser, fetch_products and size_key. Common never imports a catalog.

Cycling and tools packages own identity, category/condition rules, retailer configuration, reference-floor presets, copy and accent colors. Independent app instances/databases/static mounts avoid cross-catalog state. Fresh Powder's existing app remains intact; there is no reason to transplant snow reviews/auth/classification into new catalogs.

Flow: retailer feed -> shared parser -> local classification -> validated offers -> atomic per-source snapshot -> matching variant -> filters -> percentage order -> count/page -> rendered cards. Read-only web paths never fetch inventory. Source failures retain previous observations without refreshing their timestamps; stale data expires after 72h. Reference prices remain merchant compare-at prices; shipping/tax excluded. Tool bundle and power-platform details are conservative title-derived labels, not compatibility guarantees.

New files: shared runtime/templates/assets/tests; cycling/tools package definitions and entrypoints; refresh/preview/deployment commands; source evidence and docs. Root package discovery/check paths updated. No unrelated auth, analytics or snow migrations. Reviewable local data stays ignored, and captured small parser fixtures are explicitly dated evidence.
