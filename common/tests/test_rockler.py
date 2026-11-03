import asyncio
import json
from copy import deepcopy
from dataclasses import asdict, replace

import httpx
import pytest
from deal_common.catalog.audit import audit_sample, validate_rockler_product
from deal_common.catalog.refresh import normalize, refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.parsers.rockler import (
    RocklerParser,
    delivery_data,
    detail_data,
    listing_url,
    offer_destination,
)
from tool_deals.catalog import CATALOG

URL = 'https://www.rockler.com/test-bandsaw'


def detail(*, currency='USD', sku='77007', kind='simple', reference='2000', canonical=URL):
    config = {'#delivery-type': {'Magento_Ui/js/core/app': {'components': {'deliveryType': {
        'data': {'id': '123', 'sku': sku, 'name': 'Test Bandsaw', 'productType': kind}}}}}}
    product = {'@type': 'Product', 'name': 'Test Bandsaw', 'sku': '77007',
               'image': [{'url': 'https://www.rockler.com/media/test-bandsaw.jpg'}],
               'offers': [{'url': URL, 'price': 999, 'priceCurrency': currency,
                           'itemCondition': 'https://schema.org/NewCondition',
                           'availability': 'https://schema.org/InStock'}]}
    return (f'<link rel="canonical" href="{canonical}"><h1>Test Bandsaw</h1>'
            f'<script type="text/x-magento-init">{json.dumps(config)}</script>'
            f'<script type="application/ld+json">{json.dumps(product)}</script>'
            '<div class="product-info-main">'
            '<span id="product-price-123" data-price-type="finalPrice" data-price-amount="999">$999.00</span>'
            f'<span id="old-price-123" data-price-type="oldPrice" data-price-amount="{reference}">${reference}</span>'
            '<span id="product-price-456" data-price-type="finalPrice" data-price-amount="1">$1</span></div>'
            '<ol class="breadcrumbs"><li>Home</li><li>Band Saws</li><li>Test Bandsaw</li></ol>'
            '<table id="product-attribute-specs-table"><tr><th>Brand</th><td>Test Brand</td></tr></table>')


def stock(*, delayed=False):
    return {'delivery_available': True, 'is_stop_order': 0, 'direct_ship': int(delayed),
            'stock_message': 'Ships from Manufacturer' if delayed else 'In Stock and Ready to Ship',
            'delivery_box_message': 'Ships from Manufacturer' if delayed else 'Ready to Ship',
            'estimate_shipping_message': 'Estimated Ship Date: 11/14/2026' if delayed else '',
            'backorder_date': '11/14/2026'}


def listing(page=1, total=1):
    start = (page - 1) * 24
    end = min(start + 24, total)
    return {'pagination': {'totalResults': total, 'perPage': 24, 'currentPage': page,
                           'totalPages': (total + 23) // 24, 'begin': start + 1, 'end': end,
                           'nextPage': page + 1 if end < total else 0},
            'results': [{'uid': str(i + 123), 'name': 'Test Bandsaw', 'url': '/test-bandsaw',
                         'categories': ['Band Saws & Accessories']} for i in range(start, end)],
            'merchandising': {'content': {}}}


def test_exact_sku_reference_and_delivery_override_generic_stock():
    parser = RocklerParser()
    p = parser.parse_product_evidence(detail(), URL, json.dumps(stock(delayed=True)))[0]
    offer = p.offers[0]
    assert (offer.current_price, offer.original_price, offer.options) == (999, 2000, 'SKU 77007')
    assert offer.availability == 'unknown' and '11/14/2026' in offer.availability_note
    assert offer_destination(URL, offer.variant_key)
    assert not offer_destination(URL + '-other', offer.variant_key)
    assert normalize([p], CATALOG, 'www.rockler.com', parser_type='rockler')[0]['category'] == 'Workshop equipment'
    card = {'name': p.name, 'offer': asdict(offer)}
    result = validate_rockler_product(card, detail_data(detail(), URL), delivery_data(stock(delayed=True)))
    assert result['checks']['stock'] is False
    assert all(v for k, v in result['checks'].items() if k != 'stock')


def test_ready_to_ship_uses_active_displayed_notice_not_unused_backorder_field():
    parser = RocklerParser()
    p = parser.parse_product_evidence(detail(), URL, json.dumps(stock()))[0]
    assert p.offers[0].availability == 'in_stock'
    assert p.offers[0].availability_note == ''
    assert validate_rockler_product({'name': p.name, 'offer': asdict(p.offers[0])},
                                   detail_data(detail(), URL), delivery_data(stock()))['status'] == 'match'
    data = stock()
    data['special_shipping_message'] = '<p>Additional freight charge applies.</p>'
    assert delivery_data(data)['note'] == 'Additional freight charge applies.'


def test_displayed_decimal_price_brand_and_image_are_preserved():
    html = detail().replace('"price": 999', '"price": 1299.50')
    html = html.replace('data-price-amount="999">$999.00', 'data-price-amount="1299.50">$1,299.50')
    product = RocklerParser().parse_product_evidence(html, URL, json.dumps(stock()))[0]
    assert product.brand == 'Test Brand' and product.current_price == 1299.5
    assert product.image_url == product.offers[0].image_url == 'https://www.rockler.com/media/test-bandsaw.jpg'
    conflict = html.replace('</div>', '<span id="old-price-123" data-price-type="oldPrice" '
                            'data-price-amount="2500">$2,500</span></div>')
    with pytest.raises(ValueError, match='displayed price'):
        detail_data(conflict, URL)


@pytest.mark.parametrize('changes', [{'currency': 'CAD'}, {'sku': 'other'}, {'reference': 'NaN'},
                                     {'canonical': 'https://other.test/product'}])
def test_conflicting_detail_evidence_fails_closed(changes):
    with pytest.raises(ValueError):
        detail_data(detail(**changes), URL)


def test_bundle_unavailable_and_missing_delivery_do_not_become_exact_offers():
    parser = RocklerParser()
    assert parser.get_product_evidence_url(detail(kind='bundle'), URL) is None
    assert parser.parse_product_page(detail(kind='bundle'), URL) == []
    with pytest.raises(ValueError, match='delivery evidence'):
        parser.parse_product_page(detail(), URL)
    for value in ({}, {'delivery_available': 'true'}):
        with pytest.raises(TypeError):
            parser.parse_product_evidence(detail(), URL, json.dumps(value))
    for data in ({**stock(), 'delivery_available': False}, {**stock(), 'is_stop_order': 1}):
        assert parser.parse_product_evidence(detail(), URL, json.dumps(data)) == []


def test_full_price_promotions_skip_delivery_requests(tmp_path):
    source = RetailerConfig('Rockler', 'www.rockler.com', [listing_url()], parser_type='rockler')
    seen = []

    def handler(request):
        seen.append(request.url.path)
        if request.url.host == 'rn129l.a.searchspring.io':
            return httpx.Response(200, json=listing())
        assert request.url.path == '/test-bandsaw'
        return httpx.Response(200, text=detail(reference='999'))

    report = asyncio.run(refresh(replace(CATALOG, sources=(source,)), tmp_path / 'tools.db',
                                 delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]['status'] == 'complete' and report[0]['accepted_products'] == 0
    assert len(seen) == 2 and '/frx/stockmessage' not in seen


@pytest.mark.parametrize('failure', ['off-host', 'redirect', 'malformed'])
def test_delivery_failures_cannot_become_complete_or_contact_another_host(tmp_path, monkeypatch, failure):
    source = RetailerConfig('Rockler', 'www.rockler.com', [listing_url()], parser_type='rockler')
    seen = []
    if failure == 'off-host':
        monkeypatch.setattr(RocklerParser, 'get_product_evidence_url', lambda *args: 'https://other.test/stock')

    def handler(request):
        seen.append(str(request.url))
        if request.url.host == 'rn129l.a.searchspring.io':
            return httpx.Response(200, json=listing())
        assert request.url.host == 'www.rockler.com'
        if request.url.path == '/test-bandsaw':
            return httpx.Response(200, text=detail())
        assert request.url.path == '/frx/stockmessage'
        if failure == 'redirect':
            return httpx.Response(302, headers={'Location': 'https://other.test/stock'})
        return httpx.Response(200, json={'delivery_available': 'true'})

    report = asyncio.run(refresh(replace(CATALOG, sources=(source,)), tmp_path / 'tools.db',
                                 delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]['status'] == 'incomplete' and report[0]['accepted_products'] == 0
    assert not any('other.test' in url for url in seen)


def test_missing_delivery_identity_is_inconclusive_in_audit():
    product = RocklerParser().parse_product_evidence(detail(), URL, json.dumps(stock()))[0]
    broken = detail().replace('"data": {', '"missing": {')
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=broken))
    results = asyncio.run(audit_sample([{'name': product.name, 'store': 'Rockler',
                                        'offer': asdict(product.offers[0])}],
                                      {'Rockler': 'www.rockler.com'}, delay=0, transport=transport))
    assert results[0]['status'] == 'inconclusive'


def test_pagination_complete_and_discovery_ignores_broad_accessory_tags():
    parser = RocklerParser()
    assert parser.parse_listing_page(json.dumps(listing()), listing_url())[0].product_type is None
    assert parser.get_next_page_url(json.dumps(listing(total=25)), listing_url()) == listing_url(2)
    assert parser.get_next_page_url(json.dumps(listing(2, 25)), listing_url(2)) is None
    assert RocklerParser().get_next_page_url(json.dumps(listing(total=0)), listing_url()) is None


@pytest.mark.parametrize('case', ['short', 'duplicate', 'banner', 'total', 'page', 'cross-page-duplicate'])
def test_pagination_mismatch_never_becomes_complete(case):
    parser = RocklerParser()
    raw = listing(total=25)
    page = 1
    if case in {'total', 'page', 'cross-page-duplicate'}:
        parser.get_next_page_url(json.dumps(raw), listing_url())
        raw, page = listing(2, 25), 2
    if case == 'short':
        raw['results'].pop()
    elif case == 'duplicate':
        raw['results'][1]['uid'] = raw['results'][0]['uid']
    elif case == 'banner':
        raw['merchandising']['content']['inline'] = [{'config': {'position': {'index': 3}}}]
    elif case == 'total':
        raw['pagination']['totalResults'] = 26
    elif case == 'page':
        raw['pagination']['currentPage'] = 1
    else:
        raw['results'][0]['uid'] = '123'
    with pytest.raises(ValueError):
        parser.get_next_page_url(json.dumps(raw), listing_url(page))


def test_refresh_and_independent_audit_fetch_bound_delivery_evidence(tmp_path):
    source = RetailerConfig('Rockler', 'www.rockler.com', [listing_url()], parser_type='rockler')
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'tools.db'
    requests = []
    fail = False

    def handler(request):
        requests.append(str(request.url))
        if request.url.host == 'rn129l.a.searchspring.io':
            return httpx.Response(200, json=listing())
        if request.url.path == '/test-bandsaw':
            return httpx.Response(200, text=detail())
        assert request.url.path == '/frx/stockmessage' and request.url.params['pid'] == '123'
        return httpx.Response(403 if fail else 200, json=stock())

    transport = httpx.MockTransport(handler)
    report = asyncio.run(refresh(catalog, path, delay=0, transport=transport))
    assert report[0]['status'] == 'complete' and report[0]['evidence_requests'] == 1
    sources = read_sources(path, 'tools')
    p = sources[0]['products'][0]
    audit = asyncio.run(audit_sample([{**p, 'store': 'Rockler', 'offer': p['offers'][0]}],
                                    {'Rockler': source.domain}, delay=0, transport=transport))
    assert audit[0]['status'] == 'match'
    baseline = deepcopy(sources[0])
    fail = True
    report = asyncio.run(refresh(catalog, path, delay=0, transport=transport))
    assert report[0]['status'] == 'incomplete' and report[0]['collections'][0]['http_status'] == 403
    current = read_sources(path, 'tools')[0]
    assert (current['products'], current['successful_at']) == (baseline['products'], baseline['successful_at'])
    assert not any('/cart' in u for u in requests)
