# Competitor and organic-search audit — November 1, 2026

## Recommendation

Build FreshPowder around verified comparisons for the exact gear a shopper wants: model, season, size, condition and currency. Turn those comparisons into useful permanent product pages. Add a small set of useful brand/category landing pages and explain which price changes are actually unusual. More scraped listings alone will not deliver this advantage.

This is a research and implementation-priority document. No product changes, account connections, Search Console submissions or email delivery were made during this audit.

## Research scope and limitations

Public search queries included `snow deal`, `ski deals`, `snowboard deals`, and ski/snowboard price comparison queries. Results included SnowDeal, Ski Finder, Powder Deals, REI, evo and Backcountry. SnowDeal.io is the likely site the user remembers, but their exact Google result has not been identified conclusively. Research search results are not a controlled Google ranking report; position depends on query, location and personalization.

Directly inspected SnowDeal's rendered homepage and a product comparison in the browser. Read competitor product, deals, methodology and guide pages through web research. Some retrieved documents have older crawl dates; do not treat their prices or counts as a synchronized live market comparison. No competitor alert email delivery was tested. No backlink/traffic estimates or Search Console account data were available.

## Competitive comparison

| Site | Observed advantage | Implication for FreshPowder |
| --- | --- | --- |
| [SnowDeal](https://snowdeal.io/about) | Brand browsing, grouped merchant offers, history, favorites and comparison navigation | Build one destination per exact product instead of sending every card immediately to a retailer |
| [Ski Finder](https://www.ski-finders.com/ski/k2-mindbender-89ti) | Model-specific specifications, offers by length, history, related skis and a target-price form | Product identity and size-level offers support both buying decisions and specific search queries |
| [Ski Finder deals](https://www.ski-finders.com/deals) | Distinguishes observed price drops, previous-season closeouts and current shop-to-shop price gaps | Separate retailer list-price discounts from measured savings; explain the comparison basis |
| [Powder Deals](https://powderdeals.com/how-it-works) | Advertises email-only target-price alerts and explains its process; navigation links gear, shops, categories and guides | Add clear methodology and connected discovery pages; email delivery remains deferred per the user's instruction |
| [REI](https://www.rei.com/s/snowboard-deals) / [evo](https://www.evo.com/collections/sale-all-mountain-snowboards) | Dedicated sale pages for specific gear categories and subcategories | Compete first on useful model/brand/size searches; broad sale terms also attract major retailers |

Competitors are not uniformly better. The live [SnowDeal Vans Aura Pro page](https://snowdeal.io/c/256) showed a last update of September 3 and an explicit 59-day stale-price warning. This is one observed sample, not a site-wide accuracy finding. FreshPowder can differentiate through recent checks, clear uncertainty and strict matching. Avoid claiming a nominally cheaper offer is better when its size, season, condition or currency differs.

## FreshPowder: verified current state

- Homepage, robots.txt, sitemap and sampled category pages returned HTTP 200.
- The old Vercel hostname redirected to freshpowder.clifan.com. Canonicals on the sampled pages use the custom domain.
- The sitemap lists ten URLs: home, alerts, status, privacy and six categories. Sitemap count is not an indexed-page count.
- Category pagination uses actual links, separate URLs and self-canonicals; page 2 was not noindexed. This is a strength to preserve.
- Filter/search combinations are excluded from indexing. Do not indiscriminately turn them all into indexable pages.
- The homepage has no JSON-LD; sampled category pages have CollectionPage markup.
- Application routes have no dedicated product/model comparison pages or brand landing pages. Product titles, images and share actions point to retailer URLs.
- Default ranking favors listings with images and then retailer discount percentage. Stored price history only surfaces the immediately previous observation on cards; there is no shopper-facing history chart or evidenced rare-deal ranking.
- There are no dedicated About, methodology or contact routes in the audited application. The store report already provides useful source transparency.
- A `site:freshpowder.clifan.com` query returned no results in the research search tool. This does **not** establish Google's indexing status. Search Console inspection is needed.
- Mobile field performance, Core Web Vitals, backlinks, organic clicks and Google-selected canonicals were not measured.

## Product work, in dependency order

### 1. Normalize a small, valuable product catalog

Start with 20–30 models already present at multiple retailers. Preserve separate model seasons, men's/women's/junior variants, widths, sizes, bundles and conditions. Prefer identifiers and explicit specifications; ambiguous matches remain separate. Keep USD and CAD comparisons separate unless a clearly dated conversion is shown. Attach offer price and availability to the same variant.

Acceptance: manually review the initial matched set; add regression fixtures for similar names with different seasons, sizes, genders and bundles. A wrong comparison is more harmful than an unmatched listing.

### 2. Publish useful product pages

Proposed route family: `/products/{stable-model-slug}`. Include current offers, reported sizes, currency, checked time, historical observations, source-linked specifications and a clear retailer purchase link. Link cards and sharing to these pages while keeping a direct retailer action. Show alternatives without merging them into the same product.

Start with known history: “lowest observed since [date]” and sample coverage. Do not claim a 30/90-day or all-time low without enough observations. Preserve useful product pages when a sale ends, explain that no current offer is available, and link to alternatives.

### 3. Make the rare-deal promise measurable

Separate “below retailer list price,” “down since our last check,” and “below the normal observed price.” Rank an initial curated selection using fresh, correctly matched offers, historical context, actual size availability and savings. Cap repetitive near-identical variants. Publish the rules and limitations. Shipping and returns should be sourced and dated; unknown costs must not become zero.

Add browser-local favorites/shortlists as a low-friction return path. Keep signup email-only and explicitly coming soon until delivery is implemented; this audit does not override the earlier decision to defer sending.

## Organic-search implementation order

| Priority | Change | Verification / outcome |
| --- | --- | --- |
| P0 | Inspect or connect Search Console, submit the existing sitemap, inspect home and category URLs | Record crawl/index status, Google-selected canonical and reasons for exclusions; account access still needed if not already configured |
| P0 | Establish mobile performance and query/page baselines | Measure before optimizing; no invented Lighthouse score or ranking promise |
| P1 | Build the reviewed product pages above with server-rendered content and internal links | Every selected product is reachable without search forms or button clicks; canonical and sitemap entries agree |
| P1 | Add About, how deals are ranked, coverage limitations and a real contact route | Explain who operates the site and distinguish our price analysis from third-party gear reviews |
| P1 | Add a small set of populated brand pages and missing useful categories | Unique relevant inventory and analysis; avoid empty or near-identical combinations |
| P2 | Add accurate Product/Offer or AggregateOffer markup on eligible individual-product pages, plus breadcrumbs and site identity | Validate with Rich Results Test; markup must match visible information and currency |
| P2 | Publish original deal analysis using our observations | Example: a dated clearance-price study with sample size, methods and limitations; do not claim hands-on gear testing we have not done |
| P2 | Earn relevant discovery links through useful research and genuine partnerships | Relevant readers and referrals; no purchased link schemes or automated forum spam |

Keep the existing domain for this work; a migration is not a prerequisite. Do not count on a keyword domain, meta-keyword tags, schema alone, or more generated text to create top rankings.

Suggested initial query groups, subject to inventory and Search Console validation:

- Exact gear: `2026 K2 Mindbender 89Ti best price`, with size-specific comparison when supported.
- Brand + gear: `Burton snowboard deals`, with a dedicated page that actually helps compare relevant offers.
- Useful constraints: `ski helmets under $100`, only when there is enough fresh inventory and accurate currency filtering.
- Deal evidence: model price history, previous-season comparisons and measured price drops.

`SnowDeal` can also express brand intent, and broad `ski deals` results include travel. Do not optimize the whole site around those ambiguous phrases.

## Google guidance behind the plan

- [Search Console](https://developers.google.com/search/docs/monitor-debug/search-console-start): use indexing and query/page performance data to establish the baseline and diagnose exclusions.
- [Pagination](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading): retain crawlable links and distinct canonical URLs; control filter combinations separately.
- [Product markup](https://developers.google.com/search/docs/appearance/structured-data/product): FreshPowder is a comparison site, so assess product-snippet eligibility; merchant-listing features are for pages where customers purchase from the merchant. Never present imported review scores as our own customer-rating aggregate.
- [Helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content): original price analysis and clear sourcing should add value beyond retailer descriptions.
- [SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide): there is no guaranteed first position; changes may take weeks or months to assess. We cannot infer the cause of a competitor's ranking just from its page design.

## Success measures

Track indexed intended landing pages, non-brand search impressions/clicks, query groups reaching the top 20/top 10, click-through rate by query, retailer click-throughs, signup conversion and returning visitors. Evaluate similar page/query cohorts over time rather than a single personalized search. Also track comparison accuracy, stale offers and size coverage so search growth does not outrun data quality.

The highest-value next build is the reviewed product-comparison page system. It improves the shopping experience, creates shareable destinations, and supplies useful pages for specific searches at the same time.
