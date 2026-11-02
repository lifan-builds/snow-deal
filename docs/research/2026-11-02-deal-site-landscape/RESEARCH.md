# Research: expanding Fresh Powder into category deal sites

Research date: November 2, 2026. Recommendation: preserve the focus on the deepest percentage discounts on originally expensive goods, but validate a narrow cycling catalog before launching another site. Similar products already exist, including a publicly linked family of snow, cycling, and outdoor deal sites. The open question is whether we can repeatedly find better, usable opportunities for shoppers.

This memo combines a completed ChatGPT Deep Research investigation with direct checks of first-party competitor pages, retailer listings, affiliate documentation, and the US deceptive-pricing guides. Competitor policies are self-descriptions, not audited performance. Listing observations are snapshots, not verified checkout offers. No traffic, revenue, profitability, or market-size estimates are established here.

## What already exists

| Example | Publicly documented approach | Implication for us |
| --- | --- | --- |
| [Velo Bargains](https://velo.bargains/disclosures) | Cycling deals from partner feeds; says ranking uses percentage discount and relevance, independent of commission; claims historical checks. Its [terms](https://velo.bargains/terms) say displayed percentages use retailer-stated retail prices. | Very close to our proposal. Price-history claims and the actual denominator must be distinguished. |
| [Powder Deals](https://powderdeals.com/disclosures) | Snow-specific deals with substantially the same feed, ranking, and affiliate policy. Both sites link GearSnyper and other properties under “Our Sites.” | The category-family strategy already has a public analogue. Shared backend code is plausible but unverified; the footer does not reveal architecture or business success. |
| [trail.deals](https://trail.deals/about) | Outdoor price monitoring; publishes refresh/expiry rules, observation timestamps, and a minimum observation period before a lowest-observed badge. Accepts retailer-list markdowns or observed price drops. | A useful model for an explicit evidence contract. A short observation window must not become an “all-time low” claim. |
| [BikeHunt](https://www.bikehunt.au/guides/how-bikehunt-compares-prices) | Matches model year and equipment; shows size availability; excludes used/demo bikes from markdown badges. Prices exclude delivery. | Variant and condition handling are central to meaningful comparisons. This Australian example is a workflow reference, not a US inventory source. |
| [MTB Price Agent](https://mtbprice.com/) | Narrow full-suspension category; scores specifications against live prices; includes size filters and price alerts. | Specialization can provide useful context. Its value-score approach is different from our chosen percentage-first ranking. |
| [Slickdeals](https://slickdeals.net/corp/how-slickdeals-works/) | Community submissions and voting with editor curation. Its [support explanation](https://help.me.slickdeals.net/wiki/spaces/SS/pages/784400414) includes price history, availability, and inventory checks. | Human feedback can expose unusable or weak deals. We can initially audit top results manually without building a community platform. |
| [DealNews](https://corp.dealnews.com/faq/) | Editorial deal selection with a stated lowest-available-price standard and expired-deal handling. | A published selection rule helps explain why a deal deserves attention. It is a different standard from largest markdown against MSRP. |

The transferable pattern is collection, normalization, evidence checks, selection, distribution, and feedback. The sites differ mainly in selection and audience: community interest, editorial judgment, specification value, or discount depth. We should preserve our own selection rule rather than blend these approaches into an unexplained score.

## What the research changes

**Percentage sorting is a product choice, not a unique capability.** Even [AvantLink's product-feed tools](https://support.avantlink.com/hc/en-us/articles/4404406207501-Datafeed-Manager-Affiliate-User-Guide-Product-Datafeeds) support on-sale filtering by percentage where merchant data supplies it. Our opportunity must come from coverage, accuracy, discovery speed, or a more useful view of the available offers. These are hypotheses to measure, not advantages already demonstrated.

**The biggest percentage depends on the denominator.** Keep the formula explicit:

`discount_pct = 100 × (reference_price − offer_price) / reference_price`

Retailer list price, the retailer's actual former price, our observed historical price, and the current price at other sellers are different references. Do not silently combine them in one ranking. Initially, a clearly labeled retailer-reference markdown can remain the default, with separate historical or market comparisons when sufficient evidence exists. Suspect, mismatched, or missing references should fail eligibility rather than acquire a confident badge.

Illustrative arithmetic, not an observed offer: a product advertised at $2,000 and sold for $800 is 60% below that reference. If comparable shops sell it for $900, the advantage versus those shops is about 11%. Both figures can be correct; they answer different questions. The [FTC's deceptive-pricing guides](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-B/part-233) address artificial former prices and misleading comparisons with suggested retail prices. Merely labeling a number “MSRP” does not establish that a savings claim is sound.

**Filter for originally expensive goods without filtering out the best finds.** Prefer product-class eligibility and a defensible reference-price floor. A minimum current price can accidentally exclude the precise opportunity we want: an originally $1,000 item reduced to $200. Keep complete bikes, framesets, and components distinct. After eligibility and user filters, sort by percentage descending. Dollar savings can be a visible secondary fact and a tie-breaker; commissions and review scores should not reorder the default feed.

**A deal belongs to a purchasable variant.** A page showing “from $800,” an original price of $2,000, and sizes S–XL does not establish that every size is 60% off. Store the offer and reference for the same build, year, size, condition, currency, and seller. A one-size clearance can still be excellent for someone; label and filter it accurately rather than hiding it. Unknown stock is different from confirmed stock.

**Deepest and newest are separate dimensions.** A permanent clearance item can remain the deepest discount for months. Keep it in the percentage ranking while offering an explicit “new price drops” view or digest. Record first seen, last checked, last price change, and stock status separately. A crawler failure must not reset an item's age or imply it was just verified. Alert again only for a meaningful change, not every refresh.

**Shipping and conditions can erase the apparent advantage.** Show item-price savings separately from known shipping or mandatory assembly charges. Distinguish new, demo, refurbished, and used goods. Coupon, membership, regional, and pickup-only requirements belong beside the offer. Unknown costs remain unknown; a free-shipping promise should not be inferred from a general retailer banner.

## Is premium cycling still the best next test?

It remains a reasonable candidate because it fits expensive-product discovery and reuses much of Fresh Powder's retailer and sizing workflow. The research supports testing it; it does not establish cycling as the most profitable category.

The [Propain US outlet](https://www.propain-bikes.com/us/products/outlet/) currently advertises a Tyee frameset at 40% off/$1,000 saved and separates demo inventory. That is evidence of the intended kind of markdown, but not a checked size-specific purchase. Conversely, the [Canyon outlet](https://www.canyon.com/en-us/outlet-bikes/) snapshot shows many modest-discount and refurbished listings: the visible filters include 66 items at 10–15% off, only a few at 40%+, and substantially more refurbished than new stock. Filter counts are a changing page snapshot and do not establish disjoint inventory totals. An outlet label alone is insufficient evidence of abundant deep discounts.

MTB Price Agent's current results include several large markdowns with only XXL listed. Those are competitor listing claims, not retailer checkout confirmations. They illustrate why we need the distribution of available sizes and conditions, not just the maximum discount observed.

Start validation with new complete premium bikes, keeping framesets separate. Defer broad accessories. A narrow mountain-bike sample is reasonable, but it should not become a permanent restriction before inspecting road/gravel availability. Candidate alternatives such as premium home theater or photography deserve the same inventory audit if cycling fails; this research does not establish a winning alternative or comparable category economics.

## How the reusable methodology should work

The common asset is a consistent record of products, retailer offers, and observations. It is more valuable to preserve why a deal qualified than to reproduce a generic storefront in many colors.

| Shared responsibility | Category responsibility |
| --- | --- |
| Fetching, pagination, approved feed ingestion, retries, and source-health records | Retailer/source selection and category-specific adapters |
| Money parsing, currencies, timestamps, reference-price provenance | Product classes, exclusions, and reference-price thresholds |
| Offer/variant observations and historical changes | Model-year, build, size, condition, and compatibility normalization |
| Deduplication mechanisms and match-confidence handling | Rules for deciding when two listings describe the same product |
| Explicit discount calculation, freshness eligibility, and sorting | Filters and labels that make the offers usable in that category |
| Reusable cards, outbound attribution, and alert delivery when needed | Brand, audience, editorial guidance, and acquisition channels |

This is a recommended responsibility split, not a claim that all of these capabilities are implemented. The existing methodology document already identifies variant history, provenance, and generic UI as future work. Implement each shared capability for a demonstrated need before extracting more abstractions. A second repository or domain is not required to validate a second catalog.

For feeds, [Awin's publisher documentation](https://help.awin.com/developers/docs/product-feed-publisher-guide-intro) describes prices, shipping, discounts, and feed-update metadata. AvantLink provides structured product data and filters. These are preferable starting points where available and permitted. Network membership does not prove merchant approval, complete variant coverage, or access to every deal. Confirm program terms, permitted asset use, actual feed fields, and update lag retailer by retailer. Direct-brand and independent-shop coverage may supply incremental value, but that must be measured.

## Distribution and economics to validate

An expensive item can generate large savings while still producing little revenue for the site. Measure net approved commission after reversals, attributable orders per outbound click, and maintenance time. Do not infer profitability from a published affiliate rate, the existence of competitors, or an advertised paid subscription.

A useful accounting identity is:

`net revenue per outbound click = approved attributable commission / outbound clicks`

Use enough elapsed time for returns and attribution adjustments. Compare this with actual operating and acquisition costs, including the time required to repair sources. A generic revenue-per-click target or speculative twelve-month forecast would not answer that question.

For repeat use, test saved opportunity searches: “new medium mountain bikes, at least 50% off,” for example. This fits a shopper flexible about brand/model better than requiring them to choose a SKU before subscribing. A manually prepared digest can test usefulness before building alert infrastructure. Distribution across separate brands also requires separate audience work; shared code does not automatically supply traffic.

## Proposed next research experiment — not started

1. Sample 3–5 retailers for two weeks. Record eligible new products with a reference price of at least $1,000 and markdown of at least 40%. These are proposed research filters, not proven business thresholds or permanent product defaults. Include a mixture of specialist and direct-brand sources.
2. Audit the leading offers against product pages: matching reference, model/build/year, actual variant price, stock, condition, shipping, and restrictions. Keep rejected offers and reasons so error rates remain visible.
3. Compare qualifying offers with Velo Bargains, MTB Price Agent, and relevant broad deal results at approximately the same time. Label observations “not found in this comparison,” never “exclusive” without evidence. Separate missing products from slower discovery and incorrect variant presentation.
4. Count unique purchasable offers, new qualifying opportunities per week, size coverage, genuine price changes, errors, and minutes of manual work. Avoid counting each size or duplicate merchant listing as a separate discovery success.
5. Show a small set of real potential users the resulting digest and record which finds are useful, which constraints prevent purchase, and whether they return. Outbound clicks alone are preliminary interest, not purchase or profitable demand. Any outreach needs its own approved draft and recipients.
6. Decide whether another catalog is justified by repeated useful inventory, a measurable advantage over alternatives, manageable upkeep, and a plausible distribution route. If the inventory is mostly unavailable sizes, questionable anchors, or the same offers already well served elsewhere, revise the category or coverage before building another site.

The original Deep Research report is supporting material. This reviewed memo deliberately does not adopt its speculative market forecasts, arbitrary financial benchmarks, or a sale-price floor that could exclude exceptional bargains. This research pass makes no further application changes, starts no ongoing collection, and launches no new catalog.
