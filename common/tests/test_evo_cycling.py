import json

import pytest
from cycling_deals.catalog import CATALOG
from deal_common.catalog.refresh import normalize
from deal_common.models import Product
from deal_common.parsers.shopify import ShopifyParser


@pytest.mark.parametrize(('kind', 'category'), [
    ('Mountain Completes', 'Mountain bikes'),
    ('e-Mountain Completes', 'Electric bikes'),
    ('Gravel Completes', 'Gravel bikes'),
])
def test_complete_taxonomy_with_year_and_exact_variant_survives_normalization(kind, category):
    payload = {'products': [{'title': 'Example Complete Bike 2026', 'handle': 'bike',
        'product_type': kind, 'vendor': 'Example', 'tags': ['Free Bike Ship'],
        'options': [{'name': 'Color'}, {'name': 'Size'}], 'variants': [
            {'id': 1, 'available': False, 'price': '1000', 'compare_at_price': '4000',
             'option1': 'Red', 'option2': 'S'},
            {'id': 2, 'available': True, 'price': '2000', 'compare_at_price': '4000',
             'option1': 'Blue', 'option2': 'M'}]}]}
    parser = ShopifyParser(size_option_names=CATALOG.size_option_names,
                           size_value_pattern=CATALOG.size_value_pattern)
    products = parser.parse_listing_page(json.dumps(payload),
                                         'https://www.evo.com/collections/bikes?currency=USD')
    rows = normalize(products, CATALOG, 'www.evo.com')
    assert len(rows) == 1 and rows[0]['category'] == category
    assert [(v['variant_key'], v['size'], v['current_price'], v['original_price'], v['options'])
            for v in rows[0]['offers']] == [('2', 'M', 2000, 4000, 'Blue / M')]
    assert rows[0]['offers'][0]['url'] == 'https://www.evo.com/products/bike?currency=USD&variant=2'


@pytest.mark.parametrize('tags', [
    ('badge:Ship to Store Only',),
    ('Free Bike Ship', 'badge:Ship to Store Only'),
])
def test_ship_to_store_only_overrides_positive_shipping_tag(tags):
    product = Product('Example Complete Mountain Bike 2026', 'https://www.evo.com/products/bike',
                      2000, 4000, product_type='Mountain Completes', tags=tags)
    assert CATALOG.classify(product) is None


@pytest.mark.parametrize(('title', 'kind'), [
    ('Example Complete Mountain Bike - Blem 2026', 'Mountain Completes'),
    ('Example Used Complete Bike 2026', 'Gravel Completes'),
    ('Example Complete Wheel 2026', 'Mountain Complete Wheels'),
    ('Example Complete Bike 2026', 'Completes'),
])
def test_complete_taxonomy_keeps_condition_and_positive_category_guards(title, kind):
    product = Product(title, 'https://www.evo.com/products/bike', 2000, 4000, product_type=kind)
    assert CATALOG.classify(product) is None
