# RA Cycles purchase evidence — 2026-11-04 UTC

Scope: ten anonymous product-page reads selected from the isolated cycling candidate: four deepest frameset discounts, four top non-Framesets classifications, and two low-discount complete bikes. An additional Colnago frameset page checked the merchant's numeric `s` size labels. Requests used the existing public HTTP headers, sequential two-second pacing and no account, cart or checkout actions. All eleven product pages and the two linked policy pages returned HTTP 200. This is bounded merchant-reported evidence, not a retailer-wide quality estimate or checkout validation.

The original `/collections/bikes-on-sale` failure remains separate. The observed normal navigation's `/collections/bikes?currency=USD` collection completed through the existing Shopify path. Its 142 eligible / 64 deep products are provisional until shipping-aware ingestion and independent audit pass.

## Stock needs a source-specific detail check

Every sampled page embeds one `script.variant-status-map` beneath `div.product-info[id^="product-info-template-"]`. It maps each exact variant ID to explicit `qty`, `vw` and `available` fields. The same panel provides a selected-variant JSON literal, hidden purchase-variant input and three stock-message templates. The active selected message is identified by absence of `hidden`.

For all ten initial selected variants, the map reported positive quantity, `vw: false`, `available: true`; the hidden purchase ID and selected-variant JSON agreed with the requested key. The active message was **In Stock Ships Immediately**. The **Ships in 1–2 weeks based on its location** and **Permanently Sold Out** templates were present but hidden. A separate Coming soon reservation block also exists in the HTML. Searching unscoped page text would misread these dormant templates.

Do not enable this source through stock-blind Shopify ingestion. Keep Shopify price/variant discovery, then resolve the main product panel and bind all retained variant IDs to the status map. Confirm stock only for explicit positive quantity, available true and virtual-warehouse false. Preserve virtual-warehouse delays as unknown stock with their notice; exclude explicit unavailable variants. Missing, malformed, conflicting or incomplete map evidence must fail the source refresh. Bind the canonical product path and selected purchase ID/JSON so recommendation content cannot supply evidence. Independent auditing must include this detail check after the exact variant JSON check.

The bounded sample did not contain an active virtual-warehouse offer. Therefore the template gives its stated delay but does not establish a live delayed-variant example or prove stock accuracy for the full candidate.

## Two taxonomy and fit gaps

[OPEN ONE+ Frame](https://racycles.com/products/open-one-frame?currency=USD&variant=43594226663468) was provisionally classified as Mountain bikes. Its merchant `window.productData` tags explicitly include **Frameset**, Mountain Bikes and Open Bikes. Its description identifies the 890 g frame and included headset, rather than a complete bicycle. Give explicit Frameset taxonomy precedence over the broader bike discipline; this is not manufacturer inference.

[Colnago C59 Disc Frameset — QR/Post Mount](https://racycles.com/products/colnago-c59-disc-frameset-qr-post-mount?currency=USD&variant=44141670629420) has an explicit `fieldset[data-option="Size"]` with selected **50s**, and the selected variant JSON records `option2: "50s"`. Other rendered choices include 52s, 56cm and 54s. The 50s variant's status map reports positive quantity, nonvirtual stock and available true. Recognize the numeric-s label as an exact raw frame-size option. Do not convert it to 50cm or assert equivalent geometry.

## Condition, shipping and purchase limitations

The sampled product taxonomy, titles and main descriptions did not disclose a used/demo/refurbished or pickup-only condition. Ordinary prose uses words such as “used,” and pickup availability widgets are present; these are not evidence that the product is used or pickup-only. This sample does not establish every retailer product's condition.

Six of the ten initial pages displayed a Final Sale notice: no returns/exchanges, online-only availability, no cancellation after processing/labeling/shipping, and quality control before shipment. Preserve the actual final-sale notice; online-only is not pickup-only. Other pages show optional local pickup while also exposing shipping stock.

The linked [Returns and Exchanges policy](https://racycles.com/pages/returns-and-exchanges) describes bike assembly included in purchase price; front wheel, saddle and handlebars may arrive uninstalled. Unused/original-condition returns are generally allowed within thirty days, subject to exclusions. Factory-spec and custom-spec bikes have stated restocking fees; custom and special orders have additional cancellation limits. Final-sale item terms must take precedence over a generic return-policy summary.

The linked [International Shipping policy](https://racycles.com/pages/international-shipping-policies) states USD settlement, destination/item-dependent checkout shipping charges and estimated delivery windows. It does not prove free delivery or a delivered total for a US listing. No checkout was performed. Product prices and retailer reference prices remain distinct from independently verified historical street prices.

## Receipts

Task-owned public artifacts: `.local/source-expansion/cycling-followup-20261104/ra-review/` contains selected cards, dated HTTP receipts and response hashes, saved public pages, exact variant/map evidence, body/tag contexts, shipping/return policy receipts and sanitized main-panel excerpts. No authenticated session or browser state was used. Keep the candidate disabled until a fresh detail-aware traversal and independent merchant sample pass.

## Follow-up: observed orderable backorder and complete reference evidence

The first detail-aware candidate encountered [Van Rysel RCR Pro Ultegra Di2 Special Edition Bike](https://racycles.com/products/van-rysel-rcr-pro-ultegra-di2-special-edition-bike-6202?currency=USD). All five variants had `available: true`, `qty: 0` and `vw: false`. All three stock-message templates were hidden, while `.product-backorder .backorder` was active with a Coming soon reservation notice. These offers are orderable backorders, so they remain stock unknown. The initial candidate failure is retained; this observed fourth display state is now supported and covered by sanitized fixtures. The notice contains a hidden `.backorder__product` label naming the selected size. Exclude that identity label when preserving the common reservation message for other variants.

HTML ProductGroup schema binds every variant ID, SKU, USD current price and availability, while the selected-variant JSON and visible purchase panel bind its reference/options. Unselected references are not present in that schema. The adapter therefore uses the existing explicit product-evidence request path to read the canonical public `.js?currency=USD` product endpoint. It reconciles complete, unique IDs across the feed, HTML stock map, ProductGroup and product endpoint, then binds each exact current/reference price and option set. This adds a second paced request per product. The independent auditor can reuse its separately fetched product JSON when checking the main panel, avoiding a duplicate endpoint request.
