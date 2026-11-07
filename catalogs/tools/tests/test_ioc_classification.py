"""IOC's equipment taxonomy supplies machine identity without overriding exclusions."""
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import pytest
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.models import Product
from deal_common.parsers.shopify import ShopifyParser
from tool_deals.catalog import CATALOG, classify

ORIGIN = 'https://www.weldingsuppliesfromioc.com'
URL = ORIGIN + '/products/model'
MIG = 'Equipment/Welding/MIG Welders'
PLASMA = 'Equipment/Cutting & Plasma/Plasma Cutters'


@pytest.mark.parametrize(('kind', 'tag'), [
    ('Welding', MIG),
    ('Welding', 'Equipment/Welding/TIG Welders'),
    ('Welding', 'Equipment/Welding/Stick Welders'),
    ('Welding', 'Equipment/Welding/Multi Process'),
    ('Welding', 'Equipment/Welding/Engine Drives'),
    ('Cutting', PLASMA),
    ('Welding', PLASMA),
])
def test_observed_source_taxonomy_establishes_workshop_machine_identity(kind, tag):
    item = Product('Model 123', URL, 400, 800, product_type=kind, tags=(tag,))
    before = deepcopy(item)
    result = classify(item)
    assert result is not None
    assert (result.category, result.format, result.platform) == ('Workshop equipment', 'Not specified', '')
    assert item == before


@pytest.mark.parametrize('url', [
    'https://other.example/products/model',
    'https://www.weldingsuppliesfromioc.com.other.example/products/model',
    'https://www.weldingsuppliesfromioc.com@other.example/products/model',
    'http://www.weldingsuppliesfromioc.com/products/model',
    'https://weldingsuppliesfromioc.com/products/model',
    'https://www.weldingsuppliesfromioc.com/collections/model',
    'https://www.weldingsuppliesfromioc.com:8443/products/model',
    'https://[invalid',
])
def test_ioc_taxonomy_never_whitelists_unobserved_origins_or_collection_urls(url):
    assert classify(Product('Model 123', url, 400, 800, product_type='Welding', tags=(MIG,))) is None


@pytest.mark.parametrize(('kind', 'tags'), [
    ('Welding', ()),
    ('Welding', ('Equipment', 'Equipment/Welding')),
    ('Welding', ('MIG Welders',)),
    ('Welding', ('Equipment/Welding/Unobserved Machines',)),
    ('Cutting', (MIG,)),
    ('Machinery', (MIG,)),
    ('Tools', (PLASMA,)),
    ('Parts & Accessories', (PLASMA,)),
])
def test_generic_types_and_unqualified_taxonomy_do_not_admit_machines(kind, tags):
    assert classify(Product('Model 123', URL, 400, 800, product_type=kind, tags=tags)) is None


@pytest.mark.parametrize(('name', 'kind', 'tags'), [
    ('Demo Model', 'Welding', (MIG,)),
    ('Model', 'Welding', (MIG, 'pickup only')),
    ('Model', 'Welding', (MIG, 'pre-owned')),
    ('Spool Gun for MIG Welder', 'Welding', (MIG,)),
    ('MIG Welder Foot Control', 'Welding', (MIG,)),
    ('TIG Torch', 'Welding', ('Equipment/Welding/TIG Welders',)),
    ('Plasma Torch', 'Cutting', (PLASMA,)),
    ('Model', 'Cutting', (PLASMA, PLASMA + '/Plasma Accessories')),
    ('Model', 'Welding', (MIG, MIG + '/Parts')),
    ('Model', 'Welding', (MIG, MIG + '/Consumables')),
    ('Model', 'Cutting', (PLASMA, 'Consumables')),
    ('Plasma Cutter Replacement Cover', 'Cutting', (PLASMA,)),
])
def test_negative_condition_component_and_descendant_taxonomy_stays_prior(name, kind, tags):
    assert classify(Product(name, URL, 400, 800, product_type=kind, tags=tags)) is None


def test_complete_machine_keeps_included_torch_without_inventing_package_contents():
    result = classify(Product('Model Plasma Cutter with 20ft Hand Torch', URL, 400, 800,
                              product_type='Cutting', tags=(PLASMA,)))
    assert result is not None
    assert (result.category, result.format, result.platform) == ('Workshop equipment', 'Not specified', '')


def test_captured_feed_normalization_and_query_preserve_exact_selected_offer_facts():
    payload = json.loads((Path(__file__).parent / 'fixtures/ioc_welding.json').read_text())
    original_payload = deepcopy(payload)
    products = ShopifyParser().parse_listing_page(json.dumps(payload), ORIGIN + '/collections/all-welders?currency=USD')
    originals = deepcopy(products)
    normalized = normalize(products, CATALOG, 'www.weldingsuppliesfromioc.com')
    assert len(products) == 6 and len(normalized) == 5
    assert all(row['category'] == 'Workshop equipment' for row in normalized)
    assert not any('Interface Cable' in row['name'] for row in normalized)
    by_url = {product.url: product for product in products}
    for row in normalized:
        assert row['offers'] == [asdict(offer) for offer in by_url[row['url']].offers]
        assert row['source_category'] == by_url[row['url']].product_type
    source = {'name': 'Welding Supplies from IOC', 'successful_at': datetime.now(UTC).isoformat(),
              'products': normalized}
    filters = {'min_reference': 200, 'min_discount': 40, 'max_price': 0, 'stock': True, 'page': 1}
    result = query([source], filters)
    assert result['total'] == 2
    assert [card['name'] for card in result['cards']] == [
        'ESAB Rustler EM 280 PRO MIG Welder (0700401201)',
        'ESAB Rebel EMP 205ic AC/DC Multi-Process Welder (0558102553)',
    ]
    for card in result['cards']:
        original_offer = by_url[card['url']].offers[0]
        assert asdict(original_offer).items() <= card['offer'].items()
        assert card['offer']['discount'] == original_offer.discount_pct
    assert products == originals and payload == original_payload


def test_recognized_ioc_machine_with_unknown_stock_stays_out_of_stock_only_results():
    payload = json.loads((Path(__file__).parent / 'fixtures/ioc_welding.json').read_text())
    item = ShopifyParser().parse_listing_page(json.dumps(payload), ORIGIN + '/collections/all-welders?currency=USD')[0]
    item.offers[0].availability = 'unknown'
    original = deepcopy(item)
    normalized = normalize([item], CATALOG, 'www.weldingsuppliesfromioc.com')
    assert len(normalized) == 1 and normalized[0]['offers'] == [asdict(item.offers[0])]
    source = {'name': 'Welding Supplies from IOC', 'successful_at': datetime.now(UTC).isoformat(),
              'products': normalized}
    filters = {'min_reference': 200, 'min_discount': 40, 'max_price': 0, 'stock': False, 'page': 1}
    assert query([source], filters)['total'] == 1
    assert query([source], {**filters, 'stock': True})['total'] == 0
    assert item == original
