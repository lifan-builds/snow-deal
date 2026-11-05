"""Observed Incycle tags are source-specific; exact offers remain merchant facts."""
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cycling_deals.catalog import CATALOG, classify
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.models import Product
from deal_common.parsers.shopify import ShopifyParser

ORIGIN = 'https://www.incycle.com'
URL = ORIGIN + '/products/model'


def fixture():
    return json.loads((Path(__file__).parent / 'fixtures/incycle_bicycles.json').read_text())


@pytest.mark.parametrize(('index', 'category'), [
    (0, 'Other complete bikes'), (1, 'Electric bikes'), (2, 'Mountain bikes'),
    (3, 'Road bikes'), (4, 'Gravel bikes'), (5, 'Electric bikes'), (6, 'Framesets'),
])
def test_observed_complete_bike_tags_and_existing_frameset_precedence(index, category):
    raw = fixture()['products'][index]
    product = Product(raw['title'], ORIGIN + '/products/' + raw['handle'], 1000, 4000,
                      product_type=raw['product_type'], brand=raw['vendor'], tags=tuple(raw['tags']))
    original = deepcopy(product)
    actual = classify(product)
    assert actual is not None and actual.category == category
    assert product == original


@pytest.mark.parametrize('url', ['https://other.example/products/model', 'http://www.incycle.com/products/model',
                               'https://incycle.com/products/model', 'https://www.incycle.com.other.example/products/model',
                               'https://www.incycle.com@other.example/products/model',
                               'https://www.incycle.com/collections/model'])
def test_positive_tags_do_not_whitelist_other_origins_or_collection_paths(url):
    assert classify(Product('2023 Specialized Sirrus 4.0', url, 1000, 2000,
                            product_type='Sporting Goods', tags=('BICYCLES', 'ACTIVE'))) is None


@pytest.mark.parametrize('tags', [(), ('MOUNTAIN',), ('ELECTRIC',), ('ROAD',), ('BICYCLES',),
                                 ('BICYCLES', 'UNOBSERVED DISCIPLINE')])
def test_generic_goods_and_unqualified_tags_do_not_establish_bicycle_identity(tags):
    assert classify(Product('2023 Specialized Sirrus 4.0', URL, 1000, 2000,
                            product_type='Sporting Goods', tags=tags)) is None


@pytest.mark.parametrize('title', ['Rear Bike Rack', 'Bicycle Wheel', 'Turbo Battery', 'Bike Repair Stand',
                                 'Suspension Fork', 'Frame Cover', 'Bike Floor Pump', 'Road Bike Cable',
                                 'Bicycle Lock', 'Bike Computer', 'Bike Helmet', 'Mountain Bike Gloves',
                                 'Bicycle Rack with Free Mountain Bike'])
def test_accessory_primary_titles_cannot_borrow_complete_bike_tags(title):
    assert classify(Product(title, URL, 1000, 2000, product_type='Sporting Goods',
                            tags=('BICYCLES', 'MOUNTAIN', 'TURBO & ELECTRIC BIKE'))) is None


@pytest.mark.parametrize(('title', 'kind', 'tags'), [
    ('Demo Model', 'Sporting Goods', ('BICYCLES', 'MOUNTAIN')),
    ('Kids Model', 'Sporting Goods', ('BICYCLES', 'MOUNTAIN')),
    ('Model', 'Sporting Goods', ('BICYCLES', 'MOUNTAIN', 'no-ship', 'ship-usa')),
    ('Model', 'Sporting Goods', ('BICYCLES', 'MOUNTAIN', 'condition:open-box')),
    ('Model', 'Sporting Goods', ('BICYCLES', 'MOUNTAIN', 'badge:Ship to Store Only')),
    ('Model', 'Bike Accessories', ('BICYCLES', 'MOUNTAIN')),
    ('Model', 'Sporting Goods Accessories', ('TURBO & ELECTRIC BIKE',)),
])
def test_existing_condition_shipping_and_accessory_taxonomy_stays_prior(title, kind, tags):
    assert classify(Product(title, URL, 1000, 2000, product_type=kind, tags=tags)) is None


def test_included_accessory_and_electric_precedence_keep_primary_complete_bike():
    product = Product('Model with Rack and Lights', URL, 1000, 2000, product_type='Sporting Goods',
                      tags=('BICYCLES', 'MOUNTAIN', 'TURBO & ELECTRIC BIKE'))
    assert classify(product).category == 'Electric bikes'


def test_observed_parser_normalization_keeps_raw_variants_sizes_and_unknown_default_title():
    payload = fixture()
    original = deepcopy(payload)
    parser = ShopifyParser(size_option_names=CATALOG.size_option_names,
                           size_value_pattern=CATALOG.size_value_pattern)
    products = parser.parse_listing_page(json.dumps(payload), ORIGIN + '/collections/sale-bicycles?currency=USD')
    original_products = deepcopy(products)
    normalized = normalize(products, CATALOG, 'www.incycle.com')
    assert len(normalized) == 7
    assert {p['source_category'] for p in normalized} == {'Sporting Goods'}
    source = {'name': 'Incycle', 'successful_at': datetime.now(UTC).isoformat(), 'products': normalized}
    filters = {'min_reference': 1000, 'min_discount': 0, 'max_price': 0, 'stock': True, 'page': 1}
    result = query([source], filters, brand_aliases=CATALOG.brand_aliases)
    assert result['total'] == 7
    sirrus = next(p for p in result['cards'] if p['name'] == '2023 Specialized Sirrus 4.0')
    offer = sirrus['offer']
    assert (offer['variant_key'], offer['current_price'], offer['original_price'], offer['size'], offer['options']) == (
        '43524025319555', 799.97, 1599.99, 'XXS', 'Gloss Cactus Bloom / Satin Mystic Blue Reflective / XXS')
    assert offer['url'] == (ORIGIN + '/products/2023-specialized-sirrus-4-0?currency=USD&variant=43524025319555')
    pivot = next(p for p in result['cards'] if p['name'] == '2022 Pivot Shuttle SL Pro X01 - Large')
    assert pivot['offer']['size'] is None and pivot['offer']['options'] == ''
    assert query([source], {**filters, 'q': 'Pivot', 'size': 'Large'}, brand_aliases=CATALOG.brand_aliases)['total'] == 0
    assert query([source], {**filters, 'size': 'S1'}, brand_aliases=CATALOG.brand_aliases)['total'] == 1
    assert products == original_products and payload == original
