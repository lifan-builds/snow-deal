"""Observed generated options are excluded, never aliased to ordinary variants."""
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from cycling_deals.catalog import CATALOG
from deal_common.catalog.audit import validate_product
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.parsers.shopify import ShopifyParser, is_contender_generated_variant

ORIGIN = 'https://contenderbicycles.com'
MARKED = {'67738217840885', '67967680479477', '67967684641013', '48504718950645',
          '48790444245237', '48896550568181', '67593172910325'}


def payload():
    return json.loads((Path(__file__).parent / 'fixtures/contender_generated_options.json').read_text())


def parse(raw, origin=ORIGIN):
    return ShopifyParser(size_option_names=CATALOG.size_option_names,
                         size_value_pattern=CATALOG.size_value_pattern).parse_listing_page(
                             json.dumps(raw), origin + '/collections/sale?currency=USD')


def endpoint(item):
    """Product.js representation of the separately verified captured facts."""
    result = deepcopy(item)
    for variant in result['variants']:
        for field in ('price', 'compare_at_price'):
            variant[field] = int(Decimal(str(variant[field])) * 100)
        variant['options'] = [variant[key] for key in ('option1', 'option2', 'option3') if variant.get(key)]
    return result


def old_card(item, variant, origin=ORIGIN):
    url = origin + '/products/' + item['handle']
    return {'name': item['title'], 'url': url, 'currency': 'USD', 'offer': {
        'variant_key': str(variant['id']), 'url': url + '?currency=USD&variant=' + str(variant['id']),
        'current_price': float(variant['price']), 'original_price': float(variant['compare_at_price']),
        'options': ' / '.join(variant[key] for key in ('option1', 'option2', 'option3') if variant.get(key)),
    }}


@pytest.mark.parametrize('origin', [ORIGIN, 'https://www.contenderbicycles.com'])
def test_captured_marked_variants_disappear_and_every_surviving_ordinary_field_is_exact(origin):
    raw = payload()
    original = deepcopy(raw)
    products = parse(raw, origin)
    assert len(products) == 3
    facts = {str(v['id']): v for item in raw['products'] for v in item['variants']}
    kept = {o.variant_key: o for p in products for o in p.offers}
    assert not (set(kept) & MARKED)
    assert set(kept) == {'46988618367221', '47652505780469', '43266977104117',
                         '37271992697000', '37271992533160'}
    for product in products:
        source = next(p for p in raw['products'] if p['title'] == product.name)
        ordinary_only = {**source, 'variants': [v for v in source['variants'] if str(v['id']) not in MARKED]}
        assert asdict(product) == asdict(parse({'products': [ordinary_only]}, origin)[0])
        for offer in product.offers:
            variant = facts[offer.variant_key]
            assert (offer.current_price, offer.original_price, offer.availability) == (
                float(variant['price']), float(variant['compare_at_price']), 'in_stock')
            assert offer.size == variant['option2']
            assert offer.options == variant['option1'] + ' / ' + variant['option2']
            assert offer.url == product.url + '&variant=' + offer.variant_key
    assert raw == original


def test_actual_higher_reference_never_creates_a_discount_for_full_price_base():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-2-0-frameset')
    assert {str(v['id']) for v in item['variants']} == {'67738217840885', '47495133987061'}
    assert parse({'products': [item]}) == []  # Base remains 4200/4200, not generated 4200/4500.


def test_actual_generated_stock_never_revives_the_sold_out_black_small_base():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-upper-frameset')
    pair = [v for v in item['variants'] if str(v['id']) in {'67593172910325', '37271992664232'}]
    assert len(pair) == 2
    assert next(v for v in pair if str(v['id']) == '37271992664232')['available'] is False
    assert parse({'products': [{**item, 'variants': pair}]}) == []


def test_generated_only_products_drop_without_aliasing_to_a_guessed_base_id():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-rapha-frameset')
    item['variants'] = [v for v in item['variants'] if str(v['id']) in MARKED]
    assert parse({'products': [item]}) == []


def test_generated_extreme_discount_and_ghost_products_cannot_affect_rank_count_pages_or_sizes():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-rapha-frameset')
    marked = next(v for v in item['variants'] if str(v['id']) in MARKED)
    marked['compare_at_price'] = '10000.00'  # Synthetic inflation to expose incorrect default selection.
    competitor = deepcopy(item)
    competitor.update(handle='comparison-frameset', title='Comparison Frameset')
    competitor['variants'] = [deepcopy(v) for v in item['variants'] if str(v['id']) not in MARKED]
    competitor['variants'][0].update(id=100, price='1000.00', compare_at_price='2000.00', option2='M')
    generated_only = []
    for index in range(26):
        ghost = deepcopy(item)
        ghost.update(handle=f'generated-{index}', title=f'Generated Frameset {index}')
        ghost['variants'] = [{**marked, 'id': 900 + index}]
        generated_only.append(ghost)
    raw = {'products': [item, competitor, *generated_only]}
    original = deepcopy(raw)
    normalized = normalize(parse(raw), CATALOG, 'contenderbicycles.com')
    sources = [{'name': 'Contender', 'successful_at': datetime.now(UTC).isoformat(), 'products': normalized}]
    filters = {'min_reference': 0, 'min_discount': 0, 'max_price': 0, 'stock': True, 'page': 1}
    result = query(sources, filters)
    assert (result['total'], result['pages']) == (2, 1)
    assert [p['name'] for p in result['cards']] == ['Comparison Frameset', item['title']]
    base = result['cards'][1]
    assert base['offer']['variant_key'] == '43266977104117'
    assert (base['offer']['current_price'], base['offer']['original_price']) == (1799, 3400)
    assert base['matching_variants'] == 1
    exact = query(sources, {**filters, 'size': 'XL'})
    assert exact['total'] == 1 and exact['cards'][0]['offer']['variant_key'] == '43266977104117'
    assert query(sources, {**filters, 'size': 'XL #MWS Options 9'})['total'] == 0
    assert all('#MWS Options' not in value for value in result['facets']['size'])
    assert raw == original


def test_ordinary_unknown_stock_is_not_promoted_by_available_generated_sibling():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-rapha-frameset')
    for variant in item['variants']:
        if str(variant['id']) not in MARKED:
            variant['available'] = None
    product = parse({'products': [item]})[0]
    assert len(product.offers) == 1
    assert product.offers[0].variant_key == '43266977104117'
    assert product.offers[0].availability == 'unknown'


@pytest.mark.parametrize('field', ['title', 'option1', 'option2', 'option3', 'options'])
def test_marker_in_each_variant_field_is_bounded_and_source_scoped(field):
    value = 'M #MWS Options 12'
    variant = {field: [value] if field == 'options' else value}
    assert is_contender_generated_variant(variant, ORIGIN + '/products/model')
    assert not is_contender_generated_variant(variant, 'https://other.example/products/model')
    assert not is_contender_generated_variant(variant, 'https://contenderbicycles.com.other.example/products/model')


@pytest.mark.parametrize('value', ['MWS', 'MWS Options 1', '#MWS', '#MWS Options', '#MWS Options 1st',
                                 '#MWS Options Catalog', 'M #MWS Option 1', 'Legit#MWS Options 1'])
def test_ordinary_mws_words_and_unmarked_labels_keep_existing_behavior(value):
    variant = {'title': value, 'option1': value, 'option2': 'M'}
    assert is_contender_generated_variant(variant, ORIGIN) is False
    item = deepcopy(payload()['products'][0])
    item['variants'] = [{**variant, 'id': 100, 'price': '100', 'compare_at_price': '200', 'available': True}]
    products = parse({'products': [item]})
    assert len(products) == 1 and products[0].offers[0].variant_key == '100'
    assert products[0].offers[0].options == value + ' / M'


@pytest.mark.parametrize('origin', ['https://other.example', 'https://contenderbicycles.com.other.example'])
def test_other_merchants_retain_their_exact_generated_looking_variants(origin):
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-2-0-frameset')
    offer = parse({'products': [item]}, origin)[0].offers[0]
    assert (offer.variant_key, offer.current_price, offer.original_price, offer.size) == (
        '67738217840885', 4200, 4500, 'M #MWS Options 1')
    assert offer.url.startswith(origin + '/products/')


def test_independent_audit_rejects_marked_old_offer_even_when_every_endpoint_fact_matches():
    for item in payload()['products']:
        actual = endpoint(item)
        original = deepcopy(actual)
        for variant in item['variants']:
            if str(variant['id']) not in MARKED:
                continue
            result = validate_product(old_card(item, variant), actual, 'USD')
            assert result['status'] == 'mismatch' and result['checks']['ordinary_variant'] is False
            assert all(value for key, value in result['checks'].items() if key != 'ordinary_variant')
            assert result['merchant']['variant'] == str(variant['id'])
            assert result['merchant']['available'] is True
        assert actual == original


def test_ordinary_audit_results_and_other_hosts_keep_their_previous_fact_checks():
    item = next(p for p in payload()['products'] if p['handle'] == 'open-up-rapha-frameset')
    ordinary = next(v for v in item['variants'] if str(v['id']) not in MARKED)
    marked = next(v for v in item['variants'] if str(v['id']) in MARKED)
    expected_checks = {'identity', 'currency', 'price', 'reference', 'options', 'stock'}
    for variant, origin in [(ordinary, ORIGIN), (marked, 'https://other.example')]:
        result = validate_product(old_card(item, variant, origin), endpoint(item), 'USD')
        assert result['status'] == 'match' and set(result['checks']) == expected_checks
    ordinary['available'] = False
    result = validate_product(old_card(item, ordinary), endpoint(item), 'USD')
    assert result['status'] == 'mismatch' and result['checks']['stock'] is False
