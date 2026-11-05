# Snow savings tie correction

Fresh Powder currently chooses cheaper variants and pictured cards when exact discounts tie. Align it with the deep-discount product contract and the cycling/tools catalogs: exact percentage first, then greater cash savings within the same currency. Mixed-currency card ties group USD first, then currency code; raw USD/CAD amounts are never treated as equivalent. Existing explicit alternative sorts and selected-variant filters remain unchanged.

Scope: snow ingestion best-offer key, SQL variant selection, default card sorting and four meaningful temporary-DB regressions. The House candidate is excluded. No source configuration, schema, refresh schedule or historical observation changes.

Independent review passed and the isolated release passes 754 offline tests with zero added lint findings. Publish through CI/preview, merge, then verify the production full/partial routes against the exact public snapshot, including ordering, pagination and variant purchase links. This is a code-only ranking release; it does not renew source freshness or validate historical retailer reference prices. Roll back this commit if ordering or selection regresses; existing snapshots remain usable. Standing publication approval applies.

Status: CI and production verification pending.
