"""Public feed excerpts captured November 1, 2026; no live network in tests."""
import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from aggregator.config import StoreConfig
from aggregator.categorizer import categorize
from aggregator.scraper import _products_to_deals, scrape_store, _clean_sizes, _extract_lengths
from snow_deals.parsers.shopify import ShopifyParser

FEEDS = json.loads((Path(__file__).parent / 'fixtures/new_source_feeds.json').read_text())


def test_new_source_category_and_size_edge_cases():
    # R22 is a ski interface, not the R2 clothing-model keyword.
    assert categorize('Rossignol Hero Athlete GS 170-182 R22 Ski 2025') == 'skis'
    assert categorize('Patagonia R2 TechFace Fleece') == 'layers'
    assert _clean_sizes('NA') is None
    assert _clean_sizes('N/A, 161W') == '161W'
    assert _extract_lengths('157W, 161W') == (157, 161)
    assert _extract_lengths('148.5') == (None, None)  # Never round a reported length.


@pytest.mark.parametrize('key,url,category,price,size,brand', [
    ('utahskis', 'https://utahskis.com/collections/sale/products.json', 'bindings', 189.97, '110MM, 120MM', 'marker'),
    ('startingate', 'https://shopstartingate.com/collections/ski-boots/products.json', 'ski boots', 612.5, '27/27.5', 'armada'),
    ('freeride', 'https://www.freerideboardshop.com/en-us/collections/sale-snowboards/products.json', 'snowboards', 297, '151cm', 'bataleon'),
    ('boardom', 'https://boardom.net/collections/clearance-skis/products.json?currency=CAD', 'ski boots', 279.99, '25.5', 'full tilt'),
])
def test_reviewed_feed_preserves_real_offer(key, url, category, price, size, brand):
    deals = _products_to_deals(ShopifyParser().parse_listing_page(json.dumps(FEEDS[key]), url), key)
    assert len(deals) == 1  # Freeride's child package is excluded.
    deal = deals[0]
    assert (deal.category, deal.current_price, deal.sizes, deal.brand) == (category, price, size, brand)
    assert deal.original_price > price and deal.image_url.startswith('https://')
    if key == 'freeride':
        assert '/en-us/products/' in deal.url
    if key == 'boardom':
        assert parse_qs(urlparse(deal.url).query)['currency'] == ['CAD']


def test_market_survives_feed_pagination_and_product_links():
    parser = ShopifyParser()
    url = parser.get_api_url('https://shop.test/en-ca/collections/skis?currency=CAD', limit=1)
    assert url == 'https://shop.test/en-ca/collections/skis/products.json?limit=1&page=1&currency=CAD'
    next_url = parser.get_next_page_url('{"products":[{}]}', url)
    assert urlparse(next_url).path == urlparse(url).path
    assert parse_qs(urlparse(next_url).query) == {'limit':['1'], 'page':['2'], 'currency':['CAD']}


@pytest.mark.parametrize('markup,status', [
    ('Shopify.currency = {"active":"USD"};', 'currency_mismatch'),
    ('<html>Choose your location</html>', 'currency_unknown'),
    ('Shopify.currency = {broken};', 'currency_check_failed'),
])
def test_unverified_currency_never_enters_a_snapshot(markup, status):
    async def run():
        requests = []
        def handler(request):
            requests.append(str(request.url))
            return httpx.Response(200, text=markup)
        store = StoreConfig('Test', 'shop.test', ['https://shop.test/collections/skis?currency=CAD'],
                            currency='CAD', verify_shopify_currency=True)
        outcomes = {}
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            deals = await scrape_store(store, client, delay=0, outcomes=outcomes)
        assert deals == [] and len(requests) == 1
        assert outcomes['Test']['errors'] == 1
        assert outcomes['Test']['collections'][0]['status'] == status
    asyncio.run(run())


def test_verified_market_reaches_feed_with_currency_intact():
    async def run():
        def handler(request):
            if request.url.path.endswith('products.json'):
                assert request.url.params['currency'] == 'CAD'
                return httpx.Response(200, json=FEEDS['boardom'])
            return httpx.Response(200, text='Shopify.currency = {"active":"CAD","rate":"1.0"};')
        store = StoreConfig('Test', 'shop.test', ['https://shop.test/collections/skis?currency=CAD'],
                            currency='CAD', verify_shopify_currency=True)
        outcomes = {}
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            deals = await scrape_store(store, client, delay=0, outcomes=outcomes)
        assert len(deals) == 1
        assert deals[0].currency == 'CAD'
        assert outcomes['Test']['errors'] == 0
        assert outcomes['Test']['collections'][0]['observed_currency'] == 'CAD'
    asyncio.run(run())
