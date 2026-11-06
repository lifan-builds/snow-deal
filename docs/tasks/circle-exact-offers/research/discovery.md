# Primary source discovery — November 5, 2026 UTC

Public merchant: https://www.thecirclewhistler.com/jackson-mips-helmet.html

The current Fresh Powder card reports C$81.00 / C$269.99, stock unconfirmed, no exact variant and unavailable image. Merchant HTML and the public product endpoint agree on product 60540290 and selected XL variant 100724076 (Matte Black, SKU GR-7109606), available with tracked quantity 2 and no backorders. L variant 100724075 has quantity zero and unavailable stock. Native UI selection of XL produces `?id=100724076&quantity=1`; selecting L leaves XL selected. The JSON provides exact variant URLs directly. No cart, checkout, account or credential actions occurred.

[Lightspeed's official AJAX/JSON documentation](https://ecom-support.lightspeedhq.com/hc/en-us/articles/115002509593-3-g-AJAX-and-JSON) documents replacing the product `.html` suffix with `.ajax`; it also cautions against rapid request bursts. Retain existing two-second pacing, bounded requests and blocking/rate-limit failure behavior.

Authorized local public captures under `.local/source-expansion/circle-variants-20261105/`:

- `jackson.html.gz`: original public detail HTML, canonical/selected form, visible money, variant DOM and images.
- `jackson.ajax.json.gz`: separate public `.ajax` endpoint. Top-level product object contains id, vid, brand, price, URL/title, stock, variants and images. Each variant has its own id, SKU, price dictionary, exact URL, quoted option-label title, image ID, and stock dictionary. Explicit formatted prices carry CAD. Never borrow the top-level default price for other variants.
- `sale.html.gz` and `snow.html.gz`: first pages of the configured collections, each with 24 cards and pager advertising page 18. Actual next control is `.pager li.enabled.next a`, absent from the explicit browser next-selector. The browser also has a numbered-link fallback matching these paths, so this mismatch is not proof of a traversal defect. Active page is marked by `aria-current=true`; disabled previous/next controls must not be followed.
- `discovery.json`: sanitized single-product research and native selection observation. This is not complete-source admission.

The common HTTP fetcher requires the configured exact hostname. These merchant pages use `www.thecirclewhistler.com`, while the current browser config domain omits www. A candidate must use the canonical hostname; never relax common URL validation.

The former static parser's `.product-card` selectors are obsolete. Current cards use `.prod-card[data-product-id]`, `data-url`, `.title a`, `.product_brand`, `.price` with optional `.slashed`, and ordinary images. Listing prices are displayed CAD. Only discounted families need detail requests, but raw discovery IDs/pages must still be counted for completeness. Root is measuring complete collection coverage and request cost separately.

Implementation remains inactive until complete source and independent merchant admission. CAD offers remain outside USD inventory rankings. Preserve raw source evidence, actual timestamps and existing history.
