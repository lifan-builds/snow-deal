# Retailer feed access — 6 November 2026 UTC

Public program research only. No account created, credential inspected, application submitted, terms accepted or merchant contacted. Feed availability is a provider claim until access and actual records are verified; no source/metric added.

## Priorities

| Retailer | Primary evidence | Next evidence needed |
| --- | --- | --- |
| Acme Tools | [Official program](https://www.acmetools.com/affiliates.html) names Impact and expressly offers a full product feed after acceptance. | Approved brand relationship and representative feed covering expensive new equipment, SKU/package, USD current/reference prices, stock and timestamps. |
| Jenson USA | [Official program](https://www.jensonusa.com/our-culture/affiliate-program) links both Impact and AvantLink and advertises datafeeds. It identifies different terms for deal/coupon sites. | Verify applicable relationship and exact size/stock/destination rows; retain bike build time, oversize/geographic shipping restrictions. |
| Competitive Cyclist | [Current official program](https://www.competitivecyclist.com/info/affiliate-program) advertises a product feed and links Impact Radius. | Approved feed and exact bicycle variants; do not infer current network from older AvantLink examples. |
| Northern Tool | [Official program](https://www.northerntool.com/affiliate-program) links CJ. | Verify active program and feed availability; its public page alone does not promise variant-level feed data. |
| CPO | [Privacy policy](https://www.cpopowertools.com/privacy-policy.html) identifies Commission Junction for its affiliate program. | Current program/feed access is unconfirmed; distinguish new from reconditioned SKUs and stock. |

Acme, Jenson and Competitive Cyclist therefore form one promising Impact access track. This is an inference from their current official program pages, not proof of acceptance or available deep inventory.

## Integration approach

Use an authorized representative export before writing an adapter. Map observed records to the existing common Product/VariantOffer contracts; keep source-specific fields and catalog eligibility in the relevant catalog. Require exact selected SKU/variant, current/reference currency, condition, shipping restrictions and stock evidence. Missing sale price, ambiguous parent rows and absent stock remain unknown. Affiliate commission never changes discount ranking. A feed pull time cannot make an old source update fresh; preserve source update timestamps and expiration.

[Impact documentation](https://help.impact.com/partner/what-would-you-like-to-learn-about/platform-features/marketing-content/product-marketplace-and-catalogs/set-product-catalog-preferences-and-notifications-as-a-partner) says catalog notifications require a partnered brand granting access. [AvantLink's feed guide](https://support.avantlink.com/hc/en-us/articles/4404406207501-Datafeed-Manager-Affiliate-User-Guide-Product-Datafeeds) describes daily files and optional sale filtering. Neither proves exact stock for a merchant.

[CJ's current API](https://docs.cj.com/docs/productfeed-api-search) exposes feed summaries including productCount/lastUpdated and separate product queries; it requires publisher authorization. Use summary metadata to check coverage/freshness before any bounded product import. Do not implement against old REST examples or manufacture access identifiers.

For any granted feed, replay a complete bounded candidate, reconcile total/page uniqueness and source update age, audit independent selected purchase evidence including the fixed sample and all deep offers, preserve history, then admit. No invented discounts for free gifts, rebates, unverified coupons, used products or unavailable variants.
