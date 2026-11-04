# Tools supply follow-up — November 4, 2026 UTC

Ohio Power Tool, Laguna Tools and ToolsToday returned HTTP 403 on new public storefront probes at 05:15 UTC. No retry, bypass or source activation followed. Discount Shop Tools' three public USD collections (power tools, cordless tools, air tools) completed through the existing Shopify ingestion path but supplied no supported discounted offers. These are dated findings, not permanent availability claims.

Bolton Tools exposes readable public categories, canonical product links, model/SKU metadata, explicit USD price and new/in-stock microdata, matching visible purchase prices and stock labels. Sampled product pages include a wood saw at $1,169.11 against $2,217.60 and a magnetic drill press at $374.22 against $748.44. These are discovery observations, not admitted offers or checkout verification. Bulk-quantity prices are separate and must not become single-unit prices. Some heavy machines require freight services; keep shipping/delivery charges and electrical requirements explicit.

The full specials page contains 24,292 industrial listings, including accessories and unrelated equipment. It is not the relevant qualified cohort. The woodworking parent category reconciles 63 unique listings. The metalworking parent advertises 531 listings across eight pages, but page three repeats 22 product slugs from page two in reverse order. Selecting the site's normal Model A–Z sort changes the selected control and URLs without changing the product sequence or fixing the duplicates. Both traversals stopped and remain incomplete. Never silently deduplicate and declare this parent complete.

The next evidence step is the retailer's own twelve named metalworking subcategories. Check each complete advertised count and unique identity, then bind qualifying offers through its canonical product page. A complete child-category cohort is distinct from a claim that the broken parent traversal covered every product. No production configuration has changed.

Public task artifacts: `.local/source-expansion/tools-next-20261104/`, including the original and model-sorted failed traversals, complete Discount Shop Tools candidate receipts, three product-page examples and the child-category probe. Preserve these failures alongside any later admission evidence.

## Admission decision

The ordinary browser product page on November 4 still displays a warehouse-relocation banner: small-parcel products are unavailable and only LTL freight products may be purchased. A promised October 1 restoration date does not prove the restriction ended. The three sampled pages retain generic InStock metadata; none supplies an explicit product-specific LTL classification. Optional freight controls alone are insufficient. Bolton remains disabled. The candidate adapter rejects any nonempty relocation banner, keeping the source incomplete and preserving any earlier successful observations.

The parser has 52 focused regressions covering exact identities, single-unit versus bulk prices, USD, stock/condition, purchase controls, strict count/pagination reconciliation, audit routing and last-success retention. Sanitized fixtures describe normal markup, with the actual relocation-banner scenario separately tested. Removing a banner in an offline fixture is a decoder test, never merchant admission evidence.
