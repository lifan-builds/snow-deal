"""Cross-endpoint evidence must preserve unresolved merchant checks."""
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

import httpx
import pytest
from deal_common.catalog.audit import audit_sample
from deal_common.parsers.beaver import BeaverShopifyParser

FIXTURES = Path(__file__).parent / 'fixtures'
HTML = (FIXTURES / 'beaver-main-purchase.html').read_text()
FEED = (FIXTURES / 'beaver-feed.json').read_text()
COLLECTION = 'https://beavertools.com/collections/sales-and-closeouts?currency=USD'


@pytest.mark.parametrize('variants', [None, [], [{'id': 'absent'}]])
def test_beaver_matching_purchase_panel_cannot_resolve_missing_endpoint_variant(variants):
    parser = BeaverShopifyParser()
    listing = parser.parse_listing_page(FEED, COLLECTION)[0]
    product = parser.parse_product_page(HTML, listing.url)[0]
    card = {'name': product.name, 'store': 'Beaver Industrial Supply',
            'offer': asdict(product.offers[0])}
    raw = {**json.loads(FEED)['products'][0], 'variants': variants}
    seen = []

    def handler(request):
        seen.append(request.url.path)
        if request.url.path == '/cart.js':
            return httpx.Response(200, json={'currency': 'USD'})
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json=raw)
        return httpx.Response(200, text=HTML)

    result = asyncio.run(audit_sample([card], {'Beaver Industrial Supply': 'beavertools.com'},
                                     delay=0, transport=httpx.MockTransport(handler)))[0]
    assert result['status'] == 'inconclusive'
    assert result['reason'] in {'Malformed product response',
                                'Variant absent or ambiguous; endpoint may truncate variants'}
    assert result['checks']['product_endpoint'] is False
    assert all(value for key, value in result['checks'].items() if key.startswith('purchase_'))
    assert seen[-1] == product.url.split('?')[0].removeprefix('https://beavertools.com')


def ra_fixture_card():
    from deal_common.parsers.racycles import detail_data
    raw = json.loads((FIXTURES / 'racycles-product.json').read_text())
    html = (FIXTURES / 'racycles-purchase.html').read_text()
    url = 'https://racycles.com/products/' + raw['handle']
    data = detail_data(html, url, raw)
    key = data['selected_key']
    actual = data['variants'][key]
    card = {'name': data['name'], 'store': 'RA Cycles', 'currency': 'USD',
            'offer': {'variant_key': key, 'url': actual['url'],
                      'current_price': actual['price'], 'original_price': actual['reference'],
                      'options': actual['options'], 'size': actual['size'],
                      'availability': 'in_stock', 'availability_note': actual['shipping_note']}}
    return raw, html, card


def test_ra_independent_audit_binds_selected_size_and_purchase_stock():
    raw, html, card = ra_fixture_card()
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if request.url.path == '/cart.js':
            return httpx.Response(200, json={'currency': 'USD'})
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json=raw)
        return httpx.Response(200, text=html)

    result = asyncio.run(audit_sample([card], {'RA Cycles': 'racycles.com'},
                                     delay=0, transport=httpx.MockTransport(handler)))[0]
    assert result['status'] == 'match'
    assert result['checks']['purchase_size'] and result['checks']['purchase_stock']
    assert result['purchase_panel']['sku'] == '9752ESDN29L'
    assert seen[-1] == card['offer']['url'] and len(seen) == 3
    assert result['within_audit_window']


def test_ra_virtual_warehouse_cannot_pass_audit_with_matching_shopify_availability():
    from bs4 import BeautifulSoup
    raw, html, card = ra_fixture_card()
    soup = BeautifulSoup(html, 'html.parser')
    status_node = soup.select_one('script.variant-status-map')
    status = json.loads(status_node.string)
    status[card['offer']['variant_key']]['vw'] = True
    status_node.string = json.dumps(status)
    immediate = soup.select_one('.in-stock-message--immediate')
    immediate['hidden'] = ''
    soup.select_one('.in-stock-message--vw').attrs.pop('hidden', None)

    def handler(request):
        if request.url.path == '/cart.js':
            return httpx.Response(200, json={'currency': 'USD'})
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json=raw)
        return httpx.Response(200, text=str(soup))

    result = asyncio.run(audit_sample([card], {'RA Cycles': 'racycles.com'},
                                     delay=0, transport=httpx.MockTransport(handler)))[0]
    assert result['status'] == 'mismatch'
    assert result['checks']['stock'] is True
    assert result['checks']['purchase_stock'] is False
    assert result['purchase_panel']['virtual_warehouse'] is True
