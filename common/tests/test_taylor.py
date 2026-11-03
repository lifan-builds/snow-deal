"""Fixtures shaped from Taylor's observed listing and SKU-selection contract."""
import asyncio
import json
from dataclasses import replace

import httpx
import pytest
from deal_common.catalog.audit import audit_sample, validate_taylor_product
from deal_common.catalog.refresh import normalize, refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.models import Product
from deal_common.parsers.taylor import (
    TaylorParser,
    detail_data,
    literal,
    offer_destination,
)
from tool_deals.catalog import CATALOG, classify

URL = 'https://taytools.com/3m-grinder'
COLLECTION = 'https://taytools.com/power-tools?ppg=65535&pn=1'


def listing(total=1, ids=('32002',), page=1, size=65535):
    return (f'<span id="__productCount">{total}</span><input name="pn" value="{page}">'
            f'<select name="ppg"><option selected value="{size}">All</option></select><ul id="products">'
            + ''.join(f'<li class="product" data-product-id="{key}"><a href="{URL}?cid=2793">'
                      'Electric Angle Grinder</a><span class="price"><span class="amount">$269.00</span></span></li>'
                      for key in ids) + '</ul>')


def detail(*, variants=None, keys=None, mapping=None, currency_class='us_only', canonical=URL):
    variants = variants if variants is not None else {'4157111082': {'data': {
        'price': '269.00', 'regular_price': '494.14', 'qty': '16', 'available': True,
        'ib': False, 'level_name': 'Regular', 'vendor_sku': '111296_67115'}}}
    literals = {'skusKeyValues': variants, 'keys': keys or [], 'sc': mapping or [],
                'images': {'default': {'array': [{'normal': 'https://taytools.com/images/grinder.jpg'}]}}}
    return (f'<link rel="canonical" href="{canonical}"><h1 id="title">3M Electric Angle Grinder</h1>'
            f'<span id="price" class="{currency_class}"></span><span itemprop="itemListElement">Grinders</span>'
            '<select data-key="a_21"><option value="v_1">Small kit</option>'
            '<option value="v_2">Large kit</option></select><script>const item = {item_brand: "3M"};'
            + ''.join(f'const {key} = {json.dumps(value)};' for key, value in literals.items()) + '</script>')


def test_single_sku_price_identity_and_independent_audit():
    product = TaylorParser().parse_product_page(detail(), URL)[0]
    assert product.current_price == 269 and product.original_price == 494.14
    assert product.offers[0].variant_key == '4157111082|'
    assert product.offers[0].url == URL
    rows = normalize([product], CATALOG, 'taytools.com', parser_type='taylor')
    card = {**rows[0], 'offer': rows[0]['offers'][0]}
    assert validate_taylor_product(card, detail_data(detail(), URL))['status'] == 'match'
    card['offer']['current_price'] = 199
    assert validate_taylor_product(card, detail_data(detail(), URL))['status'] == 'mismatch'


def test_multiple_skus_keep_price_options_and_destination_together():
    a = {'price': '200', 'regular_price': '500', 'qty': '1', 'available': True,
         'ib': False, 'level_name': 'Regular', 'vendor_sku': 'KIT-S'}
    b = {**a, 'price': '450', 'vendor_sku': 'KIT-L'}
    html = detail(variants={'111': {'data': a, 'a_21': 'v_1'}, '222': {'data': b, 'a_21': 'v_2'}}, keys=['a_21'])
    p = TaylorParser().parse_product_page(html, URL)[0]
    assert [(o.current_price, o.options, o.url) for o in p.offers] == [
        (200, 'SKU KIT-S / Small kit', URL + '?a_21=v_1'),
        (450, 'SKU KIT-L / Large kit', URL + '?a_21=v_2')]
    assert p.current_price == 200
    p.offers[0].url = URL + '?a_21=v_2'
    kept = normalize([p], CATALOG, 'taytools.com', parser_type='taylor')[0]['offers']
    assert len(kept) == 1 and kept[0]['current_price'] == 450
    mapped = detail_data(detail(variants={'111': {'data': a, 'a_21': 'v_1'}},
                                keys=['a_21'], mapping={'size_x': 'a_21'}), URL)
    assert mapped['skus']['111']['query'] == 'size_x=v_1'


@pytest.mark.parametrize('quantity', [True, 'Infinity', 'NaN', None, 'unknown', 0])
def test_audit_does_not_accept_invalid_stock(quantity):
    product = TaylorParser().parse_product_page(detail(), URL)[0]
    row = normalize([product], CATALOG, 'taytools.com', parser_type='taylor')[0]
    merchant = detail_data(detail(), URL)
    merchant['skus']['4157111082']['qty'] = quantity
    result = validate_taylor_product({**row, 'offer': row['offers'][0]}, merchant)
    assert result['status'] == 'mismatch' and result['checks']['stock'] is False


@pytest.mark.parametrize('change', [{'qty': '0'}, {'available': None}, {'available': False},
                                   {'ib': True}, {'level_name': 'Factory Second'}, {'regular_price': '269'}])
def test_unknown_unavailable_backordered_or_second_stock_is_not_eligible(change):
    raw = detail_data(detail(), URL)['skus']['4157111082']
    assert TaylorParser().parse_product_page(detail(variants={'4157111082': {'data': {**raw, **change}}}), URL) == []


@pytest.mark.parametrize('value', ['nan', 'inf', True, 'invalid'])
def test_malformed_prices_fail_the_snapshot(value):
    raw = detail_data(detail(), URL)['skus']['4157111082']
    with pytest.raises(ValueError):
        TaylorParser().parse_product_page(detail(variants={'4157111082': {'data': {**raw, 'price': value}}}), URL)


@pytest.mark.parametrize('kwargs', [{'currency_class': 'ca_map'}, {'canonical': 'https://other.example/grinder'},
                                   {'variants': {}}, {'variants': {'111': {'data': {}}, '222': {'data': {}}}}])
def test_missing_currency_identity_or_unique_sku_evidence_fails(kwargs):
    with pytest.raises(ValueError):
        TaylorParser().parse_product_page(detail(**kwargs), URL)


def test_collection_completeness_uses_listing_ids_and_deduplicates_aliases_later():
    parser = TaylorParser()
    assert parser.get_next_page_url(listing(), COLLECTION) is None
    assert parser.get_next_page_url(listing(total=2, ids=('1', '2')), COLLECTION) is None
    assert len(parser.parse_listing_page(listing(total=2, ids=('1', '2')), COLLECTION)) == 2
    for html in [listing(total=2), listing(total=2, ids=('1', '1')), listing(page=2), '<html>Challenge</html>']:
        with pytest.raises(ValueError):
            parser.get_next_page_url(html, COLLECTION)
    html = listing(total=21, ids=tuple(str(n) for n in range(20)), size=20)
    assert parser.get_next_page_url(html, 'https://taytools.com/power-tools').endswith('pn=2')


@pytest.mark.parametrize('url,key', [(URL+'?a_21=v_2', '111|a_21=v_1'),
                                    (URL+'?a_21=v_1&a_21=v_1', '111|a_21=v_1'),
                                    (URL+'?redirect=evil', '111|redirect=evil'),
                                    ('https://evil.test/grinder', '111|'), (URL+'#option', '111|')])
def test_unsafe_or_mismatched_destination_is_rejected(url, key):
    assert not offer_destination(url, key)


def test_detail_requests_deduplicate_aliases_and_failed_detail_preserves_snapshot(tmp_path):
    source = RetailerConfig('Taylor Toolworks', 'taytools.com', [COLLECTION], parser_type='taylor')
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'catalog.db'
    requested = []
    def handler(request):
        requested.append(request.url.path)
        return httpx.Response(200, text=listing(total=2, ids=('1', '2')) if request.url.path == '/power-tools' else detail())
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]['status'] == 'complete' and requested == ['/power-tools', '/3m-grinder']
    before = read_sources(path, 'tools')[0]
    assert len(before['products']) == 1
    def unavailable(request):
        return httpx.Response(200, text=listing()) if request.url.path == '/power-tools' else httpx.Response(403)
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(unavailable)))
    after = read_sources(path, 'tools')[0]
    assert report[0]['status'] == 'incomplete'
    assert after['products'] == before['products'] and after['successful_at'] == before['successful_at']
    card = {**before['products'][0], 'store': 'Taylor Toolworks', 'offer': before['products'][0]['offers'][0]}
    result = asyncio.run(audit_sample([card], {'Taylor Toolworks': 'taytools.com'}, delay=0,
                                     transport=httpx.MockTransport(lambda request: httpx.Response(200, text=detail()))))
    assert result[0]['status'] == 'match'


@pytest.mark.parametrize('name', ['Tapered Drill Bits', 'Spiral Router Bits', 'Square Driver Bit'])
def test_title_only_bits_do_not_trigger_machine_detail_requests(name):
    assert classify(Product(name, URL, 100, 300)) is None


def test_powered_kit_with_bits_keeps_its_identity():
    assert classify(Product('Cordless Drill/Driver Kit with 50 Bits', URL, 200, 400)).format == 'Kit'


def test_json_literals_are_not_javascript_expressions():
    assert literal('const keys = ["a_21"];', 'keys') == ['a_21']
    with pytest.raises(ValueError):
        literal('const keys = ["a_21"].concat(extra);', 'keys')


def test_detail_budget_and_off_source_links_fail_without_publishing(tmp_path):
    from deal_common.http import fetch_products
    source = RetailerConfig('Taylor Toolworks', 'taytools.com', [COLLECTION], parser_type='taylor')
    requests = []
    async def run(html, budget):
        outcome = {'errors': 0, 'pages': 0}
        def handler(request):
            requests.append(str(request.url))
            return httpx.Response(200, text=html)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            products = await fetch_products(source, TaylorParser(), client, semaphore=asyncio.Semaphore(1),
                                            delay=0, max_product_pages=budget, outcome=outcome)
        return products, outcome
    for html, budget in [(listing(), 0), (listing().replace(URL, 'https://evil.test/grinder'), 5)]:
        products, outcome = asyncio.run(run(html, budget))
        assert not products and outcome['errors'] == 1
    assert requests == [COLLECTION, COLLECTION]
