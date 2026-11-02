# Premium cycling — proposed next catalog

Status: research proposal, not a running scraper or launched website. No brand name or deployment has been chosen.

## Why it fits

Premium bicycles and framesets combine high reference prices with deep clearance discounts. They offer the same kind of discovery as expensive skis: a shopper may accept an older model or different color to obtain a much more capable product within budget.

Public retailer listings inspected on 2026-11-02 provide concrete examples:

| Listing | Advertised reference price | Advertised sale price | Approximate discount |
| --- | ---: | ---: | ---: |
| Niner RLT 9 Apex 2025 complete bike | $2,999.99 | $1,499.94 | 50% |
| Niner RLT 9 RDO frame | $2,699.00 | From $809.95 | 70% |

Source: [Jenson USA sale listings](https://www.jensonusa.com/sale/complete-bikes?pn=0&s=price-asc). These are observed listing claims, not confirmed checkout prices or guarantees that a particular size is available. The frame and complete bike are different product classes.

There is evidence beyond one retailer: [Canyon's outlet](https://www.canyon.com/en-us/outlet-bikes/) lists past-season and used bikes, and [Propain's US outlet](https://www.propain-bikes.com/us/products/outlet/) advertises a Tyee frameset at 40% off. Those pages also demonstrate why condition must be explicit. Retailer prices and inventory change.

## Initial scope

Start with new premium mountain, gravel, and road bikes plus a separate frameset category. Use a $1,000+ reference-price filter for the validation experiment. Consider wheelsets and suspension later; cheap accessories should not overwhelm the core feed. Keep used/demo/refurbished inventory out of the initial new-product feed until condition handling is implemented.

Default ranking: deepest percentage off. Every card should show reference price, current price, dollar savings, model year, build/specification, available size, and whether it is a complete bike or frame.

Cycling rules belong here: frame size conventions, wheel sizes, groupsets/build names, suspension travel, condition, and exclusions. Shared code belongs in `common/`: platform extraction, pagination, product records, and price parsing.

## What to prove before building

- A two-week sample across 3–5 stores repeatedly yields meaningful available discounts of 40%+ on $1,000+ reference-price products.
- Sale price and reference price apply to the same model year, build, and size; “from” prices are tied to the relevant variant.
- The catalog distinguishes complete bicycles from frames, with accurate size availability.
- Oversize shipping and return restrictions are visible when known; dollar savings are not presented as a guaranteed delivered-price saving.
- Enough finds remain after filtering out unavailable stock, stale pages, demos, and misleading price anchors.

No retailer adapter or automated collection has been validated for this catalog yet.

## Other directions considered

Premium TVs/home theater also fit the expensive-item requirement; [Best Buy has an OLED clearance category](https://www.bestbuy.com/site/searchpage.jsp?browsedCategory=pcmcat1720647543741&id=pcat17071&qp=currentoffers_facet%3DCurrent+Deals~Clearance%5Etelevisiontype_facet%3DTelevision+type~OLED&st=pcmcat1720647543741_categoryid%24abcat0101000). My preference for cycling is an inference from the verified deep markdown examples and its similarity to Fresh Powder's specialist-retailer and sizing workflow, not proof of better commercial potential. TVs remain a candidate if cycling's inventory experiment is weak.
