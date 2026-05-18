"""Tests for BS4 HTML parsers using sample HTML fragments."""

from aggregator.parsers.alpineshopvt import AlpineShopVTParser
from aggregator.parsers.coloradodiscount import ColoradoDiscountParser
from snow_deals.parsers.shopify import ShopifyParser
from aggregator.parsers.sacredride import SacredRideParser


class TestAlpineShopVT:
    parser = AlpineShopVTParser()

    def test_parse_product_card(self):
        html = """
        <div class="product">
            <a href="/product/atomic-bent-100"><h4>Atomic Bent 100</h4></a>
            <div class="sale-price">$499.99</div>
            <div class="was-price">$599.99</div>
            <img src="https://example.com/img.jpg" />
        </div>
        """
        products = self.parser.parse_listing_page(html, "https://alpineshopvt.com/skis")
        assert len(products) == 1
        p = products[0]
        assert p.name == "Atomic Bent 100"
        assert p.current_price == 499.99
        assert p.original_price == 599.99

    def test_no_products(self):
        html = "<div>No products here</div>"
        assert self.parser.parse_listing_page(html, "https://example.com") == []

    def test_next_page(self):
        html = '<a rel="next" href="/page/2">Next</a>'
        assert self.parser.get_next_page_url(html, "https://example.com/page/1") == "https://example.com/page/2"

    def test_no_next_page(self):
        html = "<div>Last page</div>"
        assert self.parser.get_next_page_url(html, "https://example.com") is None


class TestColoradoDiscount:
    parser = ColoradoDiscountParser()

    def test_parse_product_li(self):
        html = """
        <ul>
        <li>
            <a href="/product/salomon-qst" title="Salomon QST 98">Buy</a>
            <a href="/product/salomon-qst">Salomon QST 98 Skis</a>
            $899.99$549.99
            <img src="https://example.com/img.jpg" />
        </li>
        </ul>
        """
        products = self.parser.parse_listing_page(html, "https://coloradodiscountskis.com/")
        assert len(products) == 1
        p = products[0]
        assert p.name == "Salomon QST 98 Skis"
        assert p.original_price == 899.99
        assert p.current_price == 549.99

    def test_no_pagination(self):
        assert self.parser.get_next_page_url("<html></html>", "https://example.com") is None


class TestSacredRide:
    parser = SacredRideParser()

    def test_parse_woocommerce_card(self):
        html = """
        <ul>
        <li class="product">
            <a href="/product/burton-custom/">
                <h2>Burton Custom Snowboard</h2>
                <span class="price">
                    <del><span class="woocommerce-Price-amount">C$649.99</span></del>
                    <ins><span class="woocommerce-Price-amount">C$519.99</span></ins>
                </span>
                <img src="https://example.com/img.jpg" />
            </a>
        </li>
        </ul>
        """
        products = self.parser.parse_listing_page(html, "https://sacredride.ca/")
        assert len(products) == 1
        p = products[0]
        assert p.name == "Burton Custom Snowboard"
        assert p.current_price == 519.99
        assert p.original_price == 649.99

    def test_next_page(self):
        html = '<a class="next page-numbers" href="/page/2/">Next</a>'
        url = self.parser.get_next_page_url(html, "https://sacredride.ca/page/1/")
        assert url == "https://sacredride.ca/page/2/"

    def test_single_price_no_sale(self):
        html = """
        <li class="product">
            <a href="/product/test/">
                <h2>Test Board</h2>
                <span class="price">
                    <span class="woocommerce-Price-amount">C$399.99</span>
                </span>
            </a>
        </li>
        """
        products = self.parser.parse_listing_page(html, "https://sacredride.ca/")
        assert len(products) == 1
        assert products[0].current_price == 399.99
        assert products[0].original_price is None

    def test_parse_current_live_markup(self):
        html = """
        <ul>
        <li class="fusion-layout-column post-card product">
            <div class="fusion-rollover">
                <div class="fusion-rollover-content">
                    <h4 class="fusion-rollover-title">
                        <a class="fusion-rollover-title-link" href="https://sacredride.ca/product/moment-wildcat-tour-118-25-26/">
                            Moment Wildcat Tour 118 25/26
                        </a>
                    </h4>
                </div>
            </div>
            <div class="fusion-post-content post-content">
                <p class="price has-sale">
                    <del aria-hidden="true"><span class="woocommerce-Price-amount amount">$1,279.95</span></del>
                    <ins aria-hidden="true"><span class="woocommerce-Price-amount amount">$1,099.95</span></ins>
                </p>
                <p class="fusion-onsale">$180.00 Off</p>
            </div>
        </li>
        </ul>
        """
        products = self.parser.parse_listing_page(html, "https://sacredride.ca/product-category/winter/skis/")
        assert len(products) == 1
        p = products[0]
        assert p.name == "Moment Wildcat Tour 118 25/26"
        assert p.url == "https://sacredride.ca/product/moment-wildcat-tour-118-25-26/"
        assert p.current_price == 1099.95
        assert p.original_price == 1279.95

    def test_next_page_from_rel_next_link(self):
        html = '<link rel="next" href="https://sacredride.ca/product-category/winter/skis/page/2/" />'
        url = self.parser.get_next_page_url(html, "https://sacredride.ca/product-category/winter/skis/")
        assert url == "https://sacredride.ca/product-category/winter/skis/page/2/"


class TestShopifyCompleteness:
    parser = ShopifyParser()

    def test_parse_available_variant_sizes_image_and_product_type(self):
        html = """
        {
          "products": [{
            "title": "Blizzard Black Pearl 88 Skis - Women's 2026",
            "handle": "253042-blizzard-black-pearl-88-skis-women-s-2026",
            "product_type": "Skis",
            "variants": [
              {"available": true, "price": "559.99", "compare_at_price": "749.99", "option1": "146 cm"},
              {"available": false, "price": "559.99", "compare_at_price": "749.99", "option1": "152 cm"}
            ],
            "images": [{"src": "https://cdn.shopify.com/example.jpg"}]
          }]
        }
        """
        products = self.parser.parse_listing_page(
            html,
            "https://www.evo.com/collections/sale-skis/products.json?limit=250&page=1",
        )
        assert len(products) == 1
        product = products[0]
        assert product.name == "Blizzard Black Pearl 88 Skis - Women's 2026"
        assert product.current_price == 559.99
        assert product.original_price == 749.99
        assert product.sizes == ["146 cm"]
        assert product.product_type == "Skis"
        assert product.image_url == "https://cdn.shopify.com/example.jpg"

    def test_shopify_api_url_accepts_smaller_limit(self):
        url = self.parser.get_api_url("https://www.evo.com/collections/sale-snowboard-boots", limit=50)
        assert url == "https://www.evo.com/collections/sale-snowboard-boots/products.json?limit=50&page=1"

    def test_shopify_next_page_uses_current_limit(self):
        html = '{"products": [%s]}' % ",".join("{}" for _ in range(50))
        next_url = self.parser.get_next_page_url(
            html,
            "https://www.evo.com/collections/sale-skis/products.json?limit=50&page=1",
        )
        assert next_url == "https://www.evo.com/collections/sale-skis/products.json?limit=50&page=2"
