import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import httpx
import pytest

from deal_common.catalog.audit import audit_sample
from deal_common.catalog.refresh import normalize, refresh
from deal_common.catalog.storage import read_sources, save_source
from deal_common.config import RetailerConfig
from deal_common.parsers.grizzly import GrizzlyParser
from tool_deals.catalog import CATALOG

URL = 'https://www.grizzly.com/products/grizzly-table-saw/g0001'
ITEM = {'@type': 'Product', 'name': '10\\u0022 Table Saw', 'sku': 'G0001', 'url': URL,
        'category': 'Table Saws', 'brand': {'name': 'Grizzly'},
        'offers': {'@type': 'Offer', 'url': URL, 'price': 500, 'priceCurrency': 'USD',
                   'availability': 'https://schema.org/InStock', 'itemCondition': 'https://schema.org/NewCondition',
                   'priceSpecification': {'price': 1500, 'priceCurrency': 'USD',
                                          'priceType': 'http://schema.org/StrikethroughPrice'}}}


def html(item=None, page=1, pages=1, *, listing=True):
    item = deepcopy(ITEM) if item is None else item
    data = {'@graph': [{'@type': 'CollectionPage', 'mainEntity': {'@type': 'ItemList',
                      'itemListElement': [{'@type': 'ListItem', 'item': item}]}}]} if listing else item
    return '<script type="application/ld+json">' + json.dumps(data) + '</script>' + (
        f'<nav id="search-pagination">Page {page} of {pages}</nav>' if listing else '')


def test_exact_sku_reference_and_currency_survive_normalization():
    parser = GrizzlyParser()
    products = parser.parse_listing_page(html(), 'https://www.grizzly.com/outlet-specials/shop-all')
    rows = normalize(products, CATALOG, 'www.grizzly.com', parser_type='grizzly')
    assert rows[0]['name'] == '10" Table Saw'
    assert rows[0]['offers'][0]['url'] == URL
    assert rows[0]['offers'][0]['variant_key'] == 'G0001'
    assert rows[0]['offers'][0]['original_price'] == 1500
    assert normalize(products, CATALOG, 'www.grizzly.com') == []
    assert normalize(products, CATALOG, 'evil.example', parser_type='grizzly') == []


@pytest.mark.parametrize('field,value', [('itemCondition', 'https://schema.org/UsedCondition'),
                                        ('availability', 'https://schema.org/BackOrder'),
                                        ('price', 'NaN'), ('url', URL + '?variant=other')])
def test_unsafe_and_unavailable_offers_are_excluded(field, value):
    item = deepcopy(ITEM)
    item['offers'][field] = value
    assert GrizzlyParser().parse_listing_page(html(item), URL) == []


def test_currency_unknown_reference_and_missing_structure_fail_safely():
    item = deepcopy(ITEM)
    item['offers']['priceCurrency'] = 'CAD'
    with pytest.raises(ValueError, match='currency'):
        GrizzlyParser().parse_listing_page(html(item), URL)
    item = deepcopy(ITEM)
    item['offers']['priceSpecification']['priceType'] = 'https://schema.org/ListPrice'
    assert GrizzlyParser().parse_listing_page(html(item), URL) == []
    with pytest.raises(ValueError, match='Missing'):
        GrizzlyParser().parse_listing_page('<html>Temporarily unavailable</html>', URL)


def test_pagination_requires_matching_page_and_explicit_last_page():
    parser = GrizzlyParser()
    url = 'https://www.grizzly.com/outlet-specials/shop-all'
    assert parser.get_next_page_url(html(page=1, pages=2), url) == url + '?cp=2'
    assert parser.get_next_page_url(html(page=2, pages=2), url + '?cp=2') is None
    with pytest.raises(ValueError, match='unexpected page'):
        parser.get_next_page_url(html(page=1, pages=2), url + '?cp=2')
    with pytest.raises(ValueError, match='pagination'):
        parser.get_next_page_url(html(listing=False), url)


def test_truncated_grizzly_refresh_keeps_previous_snapshot(tmp_path):
    path = tmp_path / 'tools.db'
    store = RetailerConfig('Grizzly Industrial', 'www.grizzly.com',
                           ['https://www.grizzly.com/outlet-specials/shop-all'], parser_type='grizzly')
    save_source(path, 'tools', store.name, '2026-11-02T00:00:00+00:00', [{'name': 'previous'}], 'complete', {})
    reports = asyncio.run(refresh(replace(CATALOG, sources=(store,)), path, max_pages=1, delay=0,
                                  transport=httpx.MockTransport(lambda r: httpx.Response(200, text=html(pages=2)))))
    assert reports[0]['status'] == 'incomplete'
    assert reports[0]['collections'][0]['status'] == 'page_limit'
    assert read_sources(path, 'tools')[0]['products'] == [{'name': 'previous'}]


@pytest.mark.parametrize('changed_price,expected', [(500, 'match'), (600, 'mismatch')])
def test_audit_fetches_separate_product_page(changed_price, expected):
    product = normalize(GrizzlyParser().parse_listing_page(html(), URL), CATALOG,
                        'www.grizzly.com', parser_type='grizzly')[0]
    card = {**product, 'store': 'Grizzly Industrial', 'offer': product['offers'][0]}
    item = deepcopy(ITEM)
    item['offers']['price'] = changed_price
    calls = []
    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(200, text=html(item, listing=False))
    result = asyncio.run(audit_sample([card], {'Grizzly Industrial': 'www.grizzly.com'}, delay=0,
                                     transport=httpx.MockTransport(handle)))
    assert calls == [URL]
    assert result[0]['status'] == expected
