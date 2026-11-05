"""Captured complete-bike taxonomy must not confuse lightweight with lights."""
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

BRANCH = 'BIKES AND FRAMES/BIKES - ELECTRIC/ELECTRIC MOUNTAIN LIGHT WEIGHT'
ORIGIN = 'https://mikesbikes.com'


def captured():
    return json.loads((Path(__file__).parent / 'fixtures/cycling_lightweight_bikes.json').read_text())


@pytest.mark.parametrize('index', [0, 1, 2])
def test_observed_heckler_habit_and_pivot_are_complete_electric_bikes(index):
    raw = captured()['products'][index]
    product = Product(raw['title'], ORIGIN + '/products/' + raw['handle'], 5000, 10000,
                      product_type=raw['product_type'], brand=raw['vendor'], tags=tuple(raw['tags']))
    original = deepcopy(product)
    assert classify(product).category == 'Electric bikes'
    assert product == original


@pytest.mark.parametrize(('title', 'kind'), [
    ('Heckler SL CC X0 Transmission Reserve', BRANCH + '/HECKLER SL/LIGHTS'),
    ('Habit Neo 1', BRANCH + '/HABIT NEO/ACCESSORIES'),
    ('Shuttle SL Pro X0 Transmission', BRANCH + '/SHUTTLE SL/FRAME PARTS'),
    ('Electric Mountain Bike', BRANCH + '/BATTERIES'),
    ('Heckler SL Battery', BRANCH + '/HECKLER SL/BATTERY'),
    ('Rear Bike Light', 'BIKES AND FRAMES/BIKE LIGHTS'),
    ('Light Weight Electric Mountain Bike', 'Bike Lights'),
    ('Electric Mountain Bike', 'ELECTRIC MOUNTAIN LIGHT WEIGHT/HECKLER SL'),
    ('Electric Mountain Bike', 'OTHER/ELECTRIC MOUNTAIN LIGHT WEIGHT/HECKLER SL'),
    ('Electric Mountain Bike', 'BIKES AND FRAMES/BIKES - ELECTRIC/ELECTRIC MOUNTAIN LIGHT WEIGHTING'),
    ('Electric Mountain Bike', 'BIKE PARTS/' + BRANCH + '/HECKLER SL'),
    ('Electric Mountain Bike', 'BIKES AND FRAMES/BIKES - ELECTRIC/LIGHTS/ELECTRIC MOUNTAIN LIGHT WEIGHT'),
    ('Mountain Bike Gloves', BRANCH + '/HECKLER SL'),
])
def test_actual_accessories_negative_descendants_and_unrelated_lightweight_kinds_stay_excluded(title, kind):
    assert classify(Product(title, ORIGIN + '/products/item', 5000, 10000, product_type=kind)) is None


@pytest.mark.parametrize(('title', 'tags', 'suffix'), [
    ('Demo Heckler SL', (), ''), ('Kids Electric Mountain Bike', (), ''),
    ('Heckler SL', ('no-ship', 'ship-usa'), ''),
    ('Heckler SL', ('ebike_block_ship',), ''),
    ('Heckler SL', ('condition:open-box',), ''),
    ('Heckler SL', (), '/JUNIOR'), ('Heckler SL', (), '/DEMO'),
])
def test_lightweight_branch_never_overrides_condition_kids_or_shipping_gates(title, tags, suffix):
    assert classify(Product(title, ORIGIN + '/products/item', 5000, 10000,
                            product_type=BRANCH + '/HECKLER SL' + suffix, tags=tags)) is None


def test_recovered_bikes_keep_raw_taxonomy_exact_variant_prices_and_stock_before_query():
    payload = captured()
    raw_original = deepcopy(payload)
    parser = ShopifyParser(size_option_names=CATALOG.size_option_names,
                           size_value_pattern=CATALOG.size_value_pattern)
    products = parser.parse_listing_page(json.dumps(payload), ORIGIN + '/collections/sale?currency=USD')
    original_products = deepcopy(products)
    normalized = normalize(products, CATALOG, 'mikesbikes.com')
    assert len(normalized) == 3
    assert [p['source_category'] for p in normalized] == [p['product_type'] for p in payload['products']]
    assert {p['category'] for p in normalized} == {'Electric bikes'}
    source = {'name': "Mike's Bikes", 'successful_at': datetime.now(UTC).isoformat(), 'products': normalized}
    filters = {'min_reference': 1000, 'min_discount': 0, 'max_price': 0, 'stock': True, 'page': 1}
    result = query([source], filters, brand_aliases=CATALOG.brand_aliases)
    assert result['total'] == 3
    assert [p['name'] for p in result['cards']] == [p['title'] for p in payload['products']]
    card = query([source], {**filters, 'size': 'XX-Large'}, brand_aliases=CATALOG.brand_aliases)['cards'][0]
    selected = card['offer']
    assert (selected['variant_key'], selected['current_price'], selected['original_price'],
            selected['size'], selected['options'], selected['availability']) == (
                '44649480650821', 4499.77, 11699.99, 'XX-Large', 'Gloss Magenta / XX-Large', 'in_stock')
    assert selected['url'] == (ORIGIN + '/products/santa-cruz-heckler-sl-cc-x0-transmission-reserve-2024'
                               '?currency=USD&variant=44649480650821')
    assert query([source], {**filters, 'size': 'Medium'}, brand_aliases=CATALOG.brand_aliases)['total'] == 0
    assert products == original_products and payload == raw_original
