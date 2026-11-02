# How Fresh Powder can win

Decision memo, November 2, 2026. This is a proposed strategy, not an implementation or deployment record.

Execution update: the [implementation receipt](execution/IMPLEMENTATION.md) records the production reconciliation, local implementation, bounded merchant checks, and remaining rollout/pilot work. In particular, production already had a 72-hour freshness gate and same-price size summaries; the source gaps below describe the earlier checkout and are not a claim about current production.

**Recommendation: establish a measurable advantage in snow first, then expand the same operating method into additional catalogs.** The presence of a close competitor is not a reason to abandon the category. It gives us a concrete experience to outperform. The promise remains exceptional percentage discounts on originally expensive products. The competitive objective is to make those opportunities accurate, understandable, and usable for the shopper's actual size and budget.

## Evidence from this inspection

I inspected Powder Deals' default deals page visually and read two product pages, compared Fresh Powder's public homepage, and inspected the current checkout's parser, query, and card code. This is a targeted qualitative audit, not a representative inventory study or a checkout-accuracy measurement.

| Observation | What it supports | What it does not prove |
| --- | --- | --- |
| Powder Deals' default [filter panel](https://powderdeals.com/deals) groups names such as Campmor and Outdoor Gear Exchange under Brands; its two category choices are Apparel and Winter Sports. | Product and merchant classification need improvement; basic shopping refinement is coarse. | Its entire underlying catalog has incorrect brand data. The inspected detail pages do identify actual manufacturers. |
| Its [Nordica Sentra listing](https://powderdeals.com/products/nordica-sentra-sl7-womens-skis-with-tpx-12-evo-bindings-2018-652328-173) says In Stock and Easy Returns, but offers no visible selectable length. Its history panel says data is being collected. | Prominent claims are easier to see than their practical limits. A shopper still needs to investigate purchase details. | That the item is unavailable, the price is false, or no internal history exists. The outbound path encountered browser verification, so retailer checkout was not confirmed. |
| The [Marmot Snowblast XL detail](https://powderdeals.com/products/marmot-snowblast-pants-men-s-black-extra-large-mrt-ap5-mt528sp-195115272883-41) displays the same amount for current price, all-time low, and 30-day average, with a Stable trend and a Buy Now message. | A lowest-observed price can be ordinary across the displayed period. We should distinguish a standing markdown from a fresh exceptional price change. | That the low claim is mathematically false or that this purchase is unsuitable. |
| At the inspected 1280 × 720 viewport, both sites consume substantial space before offer prices become visible. Fresh Powder has a quieter palette and more specific equipment navigation. | Fresh Powder has a stronger visual starting point, but shortening time to actual offers is still a useful design goal. | Measured conversion lift, mobile usability, or superiority across all screens. |
| [Fresh Powder's public homepage](https://freshpowder.clifan.com/) leads with multiple Ogasaka listings labeled 00–01. The [Keos retailer page](https://www.coloradodiscountskis.com/store/Ogasaka_Keos_1pr_Skis.html) lists $59.99 versus $1,000, describes dated geometry, and specifies buyer-paid return shipping and a 20% restocking charge. | Faithful extraction can still leave shoppers with an incomplete impression of the opportunity. Model age and restrictions matter. | That the reference price was a normal historical selling price, that stock is purchasable in every listed size, or that older gear should automatically be excluded. |

The deployed public UI differs from this checkout's templates. Source observations below apply to this checkout; they must be reconciled with the owning deployment checkout before implementation. No existing worktree was moved or changed during this strategy review.

## The customer to win first

Start with the enthusiast who knows roughly what equipment and size they need, can wait for a bargain, and is flexible about brand, color, and recent model year. Their desired outcome is: “Show me the deepest worthwhile discounts I can actually buy.”

That suggests two explicit paths. Browsing lets someone discover an unexpectedly good bargain. A saved search lets someone wait for a matching opportunity. Both preserve percentage-first ranking after the shopper's chosen filters. Neither requires turning the product into a recommendation quiz or a general-purpose gear-review publication.

Keep ski and snowboard equipment as the core experience. Clothing and accessories remain accessible without dominating the equipment feed. Do not expand into cycling merely because the shared folder structure makes it easy; the next catalog should inherit a proven shopping path and quality process.

## The product decisions

**1. Make each percentage reproducible.** Store an offer's current price, reference value and type, source, variant identity, currency, condition, and observation time. Keep advertised markdown distinct from savings against observed historical or current market prices. Use explicit eligibility rules for incomplete or mismatched comparisons. Once eligible, rank by percentage descending; do not insert an opaque quality score that changes the promised order.

**2. Make fit a first-class filter.** Preserve actual selectable sizes and their individual prices. Choosing a size must update the card's price, discount, and ordering to the eligible offer. Do not infer intermediate available lengths from a minimum and maximum. A single-size bargain remains valuable for the shopper it fits. Unknown availability should be labeled separately from confirmed availability.

**3. Present model age and condition without hiding the rules.** Old stock is not automatically bad or falsely priced. Show a clear model-year label, distinguish new-old-stock from recent clearance when known, and offer visible year/condition filters. Any proposed default age restriction should be an explicit product decision, not silent reranking. An old MSRP does not establish comparable purchasing power today.

**4. Design the first screen around actual bargains.** Retain Fresh Powder's restrained visual identity. Compress the hero, make category and size selection easy to reach, and put an actual offer's price information in the first screen on supported mobile and desktop sizes. Card hierarchy: discount, product/model year, price plus reference basis and savings, available size, merchant, check time, and material restrictions. Use consistent product imagery and compact scan-friendly cards. Keep reviews in supporting detail rather than allowing scores to overpower the bargain.

**5. Group products without flattening offers.** Show one coherent product entry with retailer and variant choices. Merge only when model, year, build, and condition match confidently. Preserve different prices by size and merchant; do not manufacture one attractive combined price. Keep direct retailer access easy, with details expandable when useful.

**6. Publish only the assurance we have earned.** Distinguish “feed observed” from “product page checked,” and do not equate either with a completed checkout. A source failure must not refresh its check time. Label a historical low with its observation window. Do not add universal Easy Returns, free shipping, or urgency badges without specific support.

These choices turn visual quality into faster decisions. The first usability test should measure whether a shopper can find a fitting opportunity and understand its constraints, not merely which screenshot they prefer.

## What can become hard to copy

A cleaner interface is useful and reproducible. The accumulating advantage would be a reliable set of product matches, variant-level observations, corrected source rules, direct relationships with shops, and an audience that returns because past finds worked.

Coverage should be selective. Map the overlap with Powder Deals and find independent or direct-brand sellers that contribute additional qualifying opportunities. Evaluate a source by usable discoveries and maintenance cost. Large feeds may cover popular stores efficiently; smaller shops might add overlooked clearance. Neither is inherently better without evidence. Good non-affiliate offers should remain eligible.

The operating loop is: detect a candidate, verify its material facts, surface it to the right shopper, observe the outcome or report, correct the relevant source rule, and retain the price/availability history. Begin with manual review of the most visible offers. The point is to discover recurring failure modes before scaling them across catalogs.

## Distribution and revenue

Make a verified find the unit of distribution. A shared page should retain category/size context and explain the offer immediately. Build a small digest of exceptional finds and saved-search notifications, with user-controlled frequency and no repeated message for an unchanged clearance price. Existing snow communities and specialist creators are sensible initial channels to test; access, attention, and conversion are not assumed. This memo authorizes no messages or posts.

Useful model and category pages can support discovery when they contain real comparison data. Avoid mass-producing near-identical landing pages before coverage and evidence justify them. Do not assume a better UI alone will generate an audience.

Keep core browsing free and convenient. Use affiliate revenue where supported, without changing ranking. Evaluate approved commission after reversals per acquired shopper and outbound click, together with retention and maintenance time. Paid acquisition should wait until observed earnings can support its cost. High ticket prices alone do not establish attractive economics, particularly for infrequent purchases.

Keep the common repository architecture. Multiple customer-facing brands are an optional distribution choice, not a requirement of code reuse. Earn one repeatable audience/quality process before multiplying domains, editorial work, and operating burden.

## The implementation sequence I recommend

1. **Establish an honest baseline.** Sample leading offers from Fresh Powder and Powder Deals for the same shopping tasks. Confirm product, selected variant, price, reference basis, availability, and material restrictions. Label blocked/unknown checks; do not count them as accurate. Inspect both high-discount outliers and ordinary offers. Record results over several days rather than claiming a market-wide conclusion from one sample.
2. **Repair our offer representation and freshness contract.** The inspected Shopify parser selects one available variant's price but combines options from multiple variants into a size list. Missing availability currently defaults to available. The inspected SQL checks length-range overlap rather than exact selectable lengths, and selects the latest store snapshot without an absolute age limit in that query. These are concrete gaps to reconcile with production and address before strong reliability claims. Preserve dated observations so a future history feature has evidence.
3. **Deliver one superior shopping path.** Category → actual size/length → deepest eligible discounts → clear offer facts → retailer. Retain selections, expose restrictions, and make the primary price facts easy to scan. Reuse existing public access, equipment navigation, and comparison work where applicable. Measure task success on mobile as well as desktop.
4. **Test repeat use with exceptional-find alerts.** The inspected live site says alerts are coming soon. Deliver a small, useful manual pilot before assuming that automated personalized alerts will retain users. Obtain consent and apply the existing approval process before outreach.
5. **Expand only when the process repeats.** A cycling pilot then tests whether a second category can reach the same accuracy and usability standard with reasonable incremental effort. Reuse the observations, eligibility, freshness, matching framework, and notification plumbing; keep category interpretation local.

Proposed acceptance targets, not external benchmarks: at least 95 of 100 sampled leading offers should match the material price/variant/availability facts at contemporaneous checking; all exclusions and unknowns should be visible in the audit. Most pilot shoppers should complete a defined find-and-understand task within one minute, with failures recorded separately when no matching inventory exists. Track voluntary returns and useful alert responses over a relevant shopping window. Small samples guide fixes; they do not establish statistical certainty or product-market fit.

Our key result is a growing number of people repeatedly finding valid, relevant, exceptional offers. Page views, raw product counts, and attractive screenshots are supporting measures. If accuracy improves but users do not return or choose us over alternatives, investigate inventory usefulness and distribution before adding another catalog.
