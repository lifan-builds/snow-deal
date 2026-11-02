# Equipment-first feed and category corrections

The default catalog includes only skis, snowboards, ski boots, snowboard boots, bindings, poles, helmets and goggles. Clothing, accessories, gloves, generic boots and uncategorized items remain available through **Include clothing & accessories**. Selecting a category explicitly also shows that category. The existing `include_clothing=1` query parameter remains compatible and now opts into the full catalog.

Title evidence now takes precedence over misleading equipment keywords: boot-cut/over-boot pants are pants, Capilene tops are layers, and replacement lenses, goggle bags, ski straps and beanies are accessories. Complete goggles with bonus lenses remain goggles. Regression cases also preserve fleece gloves and hooded jackets.

Deployment corrects clear title-based category errors in its downloaded public snapshot before computing review matches. It does not relabel prices as freshly checked or mutate the upstream release snapshot. Future scrapes use the same corrected categorizer. On the November 1 snapshot, the repair changes 155 category records, including historical rows; only category, invalid length fields and dependent review matches are affected. All other deal fields and price-history records remain unchanged.

Validation: 164 offline tests passed. Local browser checks verified the default equipment-only results, opt-in, accessory-category selection, toggling back, the screenshot examples and mobile overflow. The corrected snapshot yields 7,986 default deals; the complete catalog remains available.
