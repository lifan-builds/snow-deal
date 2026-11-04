import asyncio
import json
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path

import httpx
import pytest
from deal_common.catalog.audit import audit_sample, validate_beaver_product
from deal_common.catalog.refresh import refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.parsers.beaver import BeaverShopifyParser, detail_data
from tool_deals.catalog import CATALOG

FIXTURES = Path(__file__).parent / 'fixtures'
HTML = (FIXTURES / 'beaver-main-purchase.html').read_text()
FEED = (FIXTURES / 'beaver-feed.json').read_text()
RAW = json.loads(FEED)['products'][0]
URL = 'https://beavertools.com/products/' + RAW['handle']
COLLECTION = 'https://beavertools.com/collections/sales-and-closeouts?currency=USD'
KEY = str(RAW['variants'][0]['id'])


def parse(html=HTML):
    parser = BeaverShopifyParser()
    parser.parse_listing_page(FEED, COLLECTION + '&page=1')
    return parser.parse_product_page(html, URL + '?currency=USD')[0]


def test_exact_main_panel_retains_prices_identity_metadata_and_stock():
    product = parse()
    offer = product.offers[0]
    assert (product.name, product.brand, product.product_type) == (RAW['title'], 'Powermatic', 'Machinery')
    assert product.image_url and product.tags
    assert (offer.variant_key, offer.current_price, offer.original_price) == (KEY, 4699, 5279)
    assert offer.availability == 'in_stock' and offer.availability_note == ''
    assert offer.url == URL + '?currency=USD&variant=' + KEY
    actual = detail_data(HTML, URL + '?variant=' + KEY)
    assert actual['sku'] == 'PM1610082T' and actual['product_id'] == str(RAW['id'])


@pytest.mark.parametrize('label', ['Usually Ships in 5-7 Days', 'Call for availability', 'Backordered'])
def test_vendor_notice_overrides_feed_and_schema_instock(label):
    product = parse(HTML.replace('>\n        In Stock\n', '>\n        ' + label + '\n'))
    assert product.offers[0].availability == 'unknown'
    assert product.offers[0].availability_note == label


def test_recommendations_and_quickview_do_not_override_main_purchase_stock():
    delayed = HTML.replace('>\n        In Stock\n', '>\n        Call for availability\n')
    other = '<product-info data-view-mode="quick-view"><div class="vendor-stock-label">In Stock</div></product-info>'
    other += '<div class="product__inventory-text">Hurry, only 999 items left in stock</div>'
    assert parse(delayed + other).offers[0].availability == 'unknown'
    assert parse(HTML + other).offers[0].availability == 'in_stock'


@pytest.mark.parametrize(('before', 'after'), [
    ('4699.00', '4699.01'),
    ('$5,279.00', '$5,279.01'),
    ('"priceCurrency":"USD"', '"priceCurrency":"CAD"'),
    ('name="id" type="hidden" value="' + KEY + '"', 'name="id" type="hidden" value="123"'),
    ('data-product-id="' + str(RAW['id']) + '"', 'data-product-id="123"'),
    ('<span>PM1610082T</span>', '<span>OTHER-SKU</span>'),
    ('name="quantity" step="1"', 'name="quantity" step="2"'),
    ('https://beavertools.com/products/', 'https://evil.example/products/'),
])
def test_conflicting_identity_money_currency_or_quantity_is_not_admitted(before, after):
    assert before in HTML
    with pytest.raises(ValueError):
        parse(HTML.replace(before, after))


def test_ambiguous_or_missing_panel_and_selected_variant_fail_closed():
    for html in ('', HTML + HTML, HTML.replace('class="vendor-stock-label', 'class="missing-stock')):
        with pytest.raises(ValueError):
            parse(html)
    with pytest.raises(ValueError, match='selected variant'):
        detail_data(HTML, URL + '?variant=123')
    with pytest.raises(ValueError):
        detail_data(HTML, 'https://evil.example/products/' + RAW['handle'])


def test_multiple_variants_or_purchasable_options_require_supported_selection():
    script_start = HTML.index('<script>window.dpoData = {product:')
    script_end = HTML.index('};</script>', script_start)
    raw = json.loads(HTML[script_start + len('<script>window.dpoData = {product:'):script_end])
    raw['variants'].append({**raw['variants'][0], 'id': 999})
    changed = HTML[:script_start] + '<script>window.dpoData = {product:' + json.dumps(raw) + HTML[script_end:]
    with pytest.raises(ValueError, match='multiple variants'):
        parse(changed)
    with pytest.raises(ValueError, match='product options'):
        parse(HTML.replace('"options": ["Default Title"]', '"options": ["220V"]'))


def test_disabled_button_cannot_confirm_stock():
    assert parse(HTML.replace('name="add"', 'name="add" disabled')).offers[0].availability == 'unknown'


@pytest.mark.parametrize(('before', 'after'), [
    ('schema.org\\/InStock', 'schema.org\\/OutOfStock'),
    ('"available": true', '"available": false'),
    ('>\n        In Stock\n', '>\n        Sold Out\n'),
])
def test_explicit_unavailable_detail_is_removed_despite_available_feed(before, after):
    changed = HTML.replace(before, after)
    assert changed != HTML
    parser = BeaverShopifyParser()
    parser.parse_listing_page(FEED, COLLECTION + '&page=1')
    assert parser.parse_product_page(changed, URL + '?currency=USD') == []


def test_complete_refresh_preserves_notice_and_failed_detail_preserves_last_good_snapshot(tmp_path):
    source = RetailerConfig('Beaver Industrial Supply', 'beavertools.com', [COLLECTION], verify_shopify_currency=True)
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'tools.db'
    def handler(request):
        if '/collections/' in request.url.path:
            if request.url.path.endswith('.json'):
                return httpx.Response(200, text=FEED)
            return httpx.Response(200, text='<script>Shopify.currency = {"active":"USD"};</script>')
        return httpx.Response(200, text=HTML.replace('>\n        In Stock\n', '>\n        Usually Ships in 5-7 Days\n'))
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]['status'] == 'complete'
    before = read_sources(path, 'tools')[0]
    assert before['products'][0]['offers'][0]['availability'] == 'unknown'
    assert before['products'][0]['offers'][0]['availability_note'] == 'Usually Ships in 5-7 Days'
    def failed(request):
        if '/products/' in request.url.path:
            return httpx.Response(200, text='<html>Unavailable</html>')
        return handler(request)
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(failed)))
    assert report[0]['status'] == 'incomplete'
    after = read_sources(path, 'tools')[0]
    assert after['successful_at'] == before['successful_at']
    assert after['products'] == before['products']


def test_fein_model_without_conditional_shipping_script_uses_product_literal():
    html = (FIXTURES / 'beaver-fein-purchase.html').read_text()
    actual = detail_data(html, 'https://beavertools.com/products/71293661090-fein-18v-amm700-kit-w-2-4ah-procore-batteries-charger-full-accessory-kit-in-l-box')
    assert actual['variant_key'] == '44153153290333'
    assert actual['name'].startswith('Fein MULTIMASTER') and actual['price'] == 499.95


def test_independent_audit_refetches_main_panel_after_matching_variant_json():
    product = parse()
    card = {'name': product.name, 'store': 'Beaver Industrial Supply', 'offer': asdict(product.offers[0])}
    raw = deepcopy(RAW)
    variant = raw['variants'][0]
    variant.update(price=469900, compare_at_price=527900, options=['Default Title'])
    seen = []
    def handler(request):
        seen.append(str(request.url))
        if request.url.path == '/cart.js':
            return httpx.Response(200, json={'currency': 'USD'})
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json=raw)
        return httpx.Response(200, text=HTML)
    result = asyncio.run(audit_sample([card], {'Beaver Industrial Supply': 'beavertools.com'},
                                     delay=0, transport=httpx.MockTransport(handler)))[0]
    assert result['status'] == 'match' and all(result['checks'].values())
    assert result['product_evidence_url'] == card['offer']['url']
    assert result['product_response_sha256'] and len(seen) == 3
    assert seen[-1] == card['offer']['url']
    delayed = HTML.replace('>\n        In Stock\n', '>\n        Usually Ships in 5-7 Days\n')
    actual = detail_data(delayed, card['offer']['url'])
    comparison = validate_beaver_product(card, actual)
    assert comparison['status'] == 'mismatch' and comparison['checks']['stock'] is False
    def delayed_handler(request):
        return httpx.Response(200, text=delayed) if not request.url.path.endswith('.js') else handler(request)
    result = asyncio.run(audit_sample([card], {'Beaver Industrial Supply': 'beavertools.com'},
                                     delay=0, transport=httpx.MockTransport(delayed_handler)))[0]
    assert result['status'] == 'mismatch'
    assert result['checks']['stock'] and result['checks']['price']
    assert result['checks']['purchase_stock'] is False
