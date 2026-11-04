# Discount precision

The shared discount function rounds to one decimal before selection, filtering and ranking. A $2,220.10 offer against $3,699 therefore passes a 40% minimum even though its discount is below 40%. Rounded ties can also let savings or images outrank a higher actual percentage. Snow's selectable and legacy rows persist rounded values.

Use one shared calculation from decimal price inputs, returning an unrounded numeric percentage. Product and VariantOffer use it. The shared cycling/tools query already calls this function before selection. Snow must call the same function in its read query for selectable offers and legacy product rows, rather than trust historical cached percentages. Register the function on both list and count connections. Keep price, reference, stock, size and URL bound to the selected variant.

Change boundary: shared offers/models, snow offers/query registration, targeted regression tests and methodology/parser contracts. Templates already format percentages; retain their presentation. No schema migration, historical observation rewriting, ranking tie-break changes, source admission or price/reference inference. Existing queued release heads stay frozen.

Verify below/exact/above threshold prices, rounded ranking ties, selected-variant filtering/count/pagination, read-only old snapshots and legacy snow rows. Quantify changed counts from explicitly downloaded public release artifacts; preserve earlier receipts as historical evidence. Run the complete offline suite and CI lint before publication.

Release after the queued source and audit releases, with their terminal rollout receipts and passing CI. Refresh/audit/package/deploy all three catalogs under standing authorization. Rollback to the preceding verified release using its retained public snapshots; never bootstrap or discard history.
