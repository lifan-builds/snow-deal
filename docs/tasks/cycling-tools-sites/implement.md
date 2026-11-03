# Execution

1. Inspect shared contracts and verify candidate source URLs.
2. Implement shared snapshot/query/refresh/application boundary.
3. Add cycling and tools definitions and distinct storefronts.
4. Test adversarial filtering, source failure preservation, isolation and rendering.
5. Collect bounded real inventories through supported public feeds; record source limits.
6. Run offline regression suite, package checks, browser shopping/mobile checks.
7. Record exact launch destinations/configuration for publication approval after previews are ready.


## Completion evidence

- Shared runtime and both catalog sites implemented; separate branded assets remain in each catalog package.
- 277 offline tests, scoped Ruff, JavaScript syntax, Python compilation and whitespace checks pass.
- Wheel built and installed into a task-owned target; both CLI entrypoints work. Standalone bundle smoke tests pass.
- Live source validation: 249 cycling deals at the default floor across two retailers; 71 tools deals from Woodcraft.
- Desktop and 390px mobile previews inspected. Exact-size query, kit query, local saved search, no horizontal overflow, and no browser console errors verified.
- Latest local deploy directories: `.local/catalog-preview/bigring-final` and `.local/catalog-preview/benchdrop-final`.
- User-facing previews remain on ports 8766 and 8767. Nothing pushed or publicly deployed; see DELIVERY.md for launch requirements and coverage limits.
