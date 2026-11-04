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
