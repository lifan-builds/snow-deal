"""Exact price/size/link binding and fail-closed collection traversal."""
import asyncio
import copy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from deal_common.config import RetailerConfig
from deal_common.http import fetch_products
from deal_common.parsers.skiessentials import (
    SkiEssentialsParser,
    _product,
    collection_identity,
)

URL = 'https://www.skiessentials.com/collections/alpine-skis'
TABLE = [{'_1': 2}, 'loaderData', {'_3': 4}, 'routes/collections.$handle',
         {'_5': 6}, 'collection', {'_7': 8, '_9': 10}, 'id',
         'gid://shopify/Collection/434300354856', 'handle', 'alpine-skis']


def html(table=None):
    return '<script>window.__reactRouterContext.streamController.enqueue(' + json.dumps(json.dumps(TABLE if table is None else table)) + ');</script>'


@pytest.fixture
def item():
    return json.loads((Path(__file__).parent / 'fixtures/skiessentials-xo.json').read_text())


def feed(items, total=None):
    return json.dumps({'products': items, 'total_product': len(items) if total is None else total})


def start():
    parser = SkiEssentialsParser()
    assert parser.parse_listing_page(html(), URL) == []
    return parser, parser.get_next_page_url(html(), URL)


def test_exact_sku_sale_stock_and_destination(item):
    product = _product(item)
    assert product.url.endswith('/products/2024-xo-h21-ski-skxo0187h21')
    assert product.current_price == 199
    assert product.original_price == 1250
    assert product.brand == 'XO Skis'
    assert product.image_url.startswith('https://')
    assert [(o.variant_key, o.size, o.availability) for o in product.offers] == [
        ('47335044645160', '166', 'in_stock'), ('47335044710696', '178', 'in_stock')]
    assert parse_qs(urlsplit(product.offers[1].url).query) == {'ski size': ['178']}
    assert all(o.current_price != float(item['variants'][0]['price_usd']) for o in product.offers)


def test_each_sku_keeps_own_price(item):
    prices = json.loads(item['metafields'][0]['value'])
    prices[item['variants'][2]['sku']] = 400
    item['metafields'][0]['value'] = json.dumps(prices)
    product = _product(item)
    assert [(o.size, o.current_price) for o in product.offers] == [('166', 199), ('178', 400)]
    assert product.current_price == 199


@pytest.mark.parametrize('patch', [
    {'available': None}, {'inventory_quantity': 0}, {'inventory_quantity': -1},
    {'inventory_quantity': True}, {'inventory_quantity': None},
    {'inventory_management': None}, {'inventory_policy': 'continue'},
])
def test_conflicting_or_unknown_stock_never_confirms_fit(item, patch):
    item['variants'][0].update(patch)
    product = _product(item)
    assert product.offers[0].availability == 'unknown'
    assert '166' not in (product.sizes or [])


@pytest.mark.parametrize('value', [None, True, -199, 'NaN', 'inf', '199 USD', '199junk'])
def test_invalid_sku_prices_are_not_replaced_with_lowest_price(item, value):
    prices = json.loads(item['metafields'][0]['value'])
    prices[item['variants'][0]['sku']] = value
    item['metafields'][0]['value'] = json.dumps(prices)
    assert [o.size for o in _product(item).offers] == ['178']


def test_foreign_currency_or_malformed_metadata_fails(item):
    item['metafields'][1]['value'] = '{"amount":199,"currency_code":"CAD"}'
    with pytest.raises(ValueError, match='USD'):
        _product(item)
    item['metafields'][1]['value'] = 'not json'
    with pytest.raises(ValueError):
        _product(item)


def test_bundles_and_unverified_option_names_are_not_exact_offers(item):
    bundle = copy.deepcopy(item)
    bundle['tags'].append('Bundle Product')
    assert _product(bundle) is None
    item['variants'][0]['merged_options'] = ['option:166']
    assert [o.size for o in _product(item).offers] == ['178']


def test_ambiguous_options_or_identity_fail(item):
    item['variants'][2]['merged_options'] = ['ski_size:166']
    with pytest.raises(ValueError, match='destination'):
        _product(item)
    item['handle'] = '../elsewhere'
    with pytest.raises(ValueError, match='identity'):
        _product(item)


def test_collection_identity_is_bounded_data_only():
    assert collection_identity(html(), 'alpine-skis') == '434300354856'
    with pytest.raises(ValueError):
        collection_identity(html(), 'snowboards')
    for bad in [[], [{'_1': -1}, 'loaderData'], [{'_999': 1}], [{'_1': 0}, 'loaderData']]:
        with pytest.raises((ValueError, TypeError)):
            collection_identity(html(bad), 'alpine-skis')


def test_complete_collection_and_reset(item):
    parser, url = start()
    assert len(parser.parse_listing_page(feed([item]), url)) == 1
    assert parser.get_next_page_url('', url) is None
    assert len(parser.seen) == 1
    parser.parse_listing_page(html(), URL)
    assert parser.seen == set()


@pytest.mark.parametrize('change', ['total', 'repeat', 'truncated', 'out_of_order'])
def test_incomplete_or_changing_feed_fails(change):
    parser, url = start()
    bundles = [{'id': i, 'tags': ['Bundle Product']} for i in range(48)]
    parser.parse_listing_page(feed(bundles, 49), url)
    second = parser.get_next_page_url('', url)
    items, total = [{'id': 48, 'tags': ['Bundle Product']}], 49
    if change == 'total':
        total = 50
    elif change == 'repeat':
        items[0]['id'] = 0
    elif change == 'truncated':
        items = []
    else:
        second = url
    with pytest.raises(ValueError):
        parser.parse_listing_page(feed(items, total), second)


def test_fetcher_reports_truncated_source_instead_of_success():
    def response(request):
        if request.url.host == 'www.skiessentials.com':
            return httpx.Response(200, text=html())
        return httpx.Response(200, json={'total_product': 2, 'products': []})
    source = RetailerConfig('Ski Essentials', 'skiessentials.com', [URL], parser_type='skiessentials')
    outcome = {'pages': 0, 'errors': 0}
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
            return await fetch_products(source, SkiEssentialsParser(), client,
                                          semaphore=asyncio.Semaphore(1), delay=0, max_pages=25, outcome=outcome)
    result = asyncio.run(run())
    assert result == []
    assert outcome['errors'] == 1
    assert outcome['collections'][0]['status'] == 'parse_error'
