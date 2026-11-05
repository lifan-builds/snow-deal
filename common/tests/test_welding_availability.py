"""Sanitized captured Baker's sentence; deliberately synthetic stock conflicts."""
import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import pytest
from deal_common.catalog.audit import validate_product
from deal_common.parsers.shopify import ShopifyParser

BAKERS = 'https://bakersgas.com'
CYBER = 'https://store.cyberweld.com'


def item():
    return json.loads((Path(__file__).parent / 'fixtures/bakers_backorder.json').read_text())


def parse(raw, origin=BAKERS):
    return ShopifyParser().parse_listing_page(json.dumps({'products': [raw]}),
                                             origin + '/collections/machines?currency=USD')[0]


def endpoint(raw):
    actual = deepcopy(raw)
    actual['description'] = actual.pop('body_html', '')
    for variant in actual['variants']:
        variant['options'] = [variant['option1']]
        variant['price'] = int(float(variant['price']) * 100)
        variant['compare_at_price'] = int(float(variant['compare_at_price']) * 100)
    return actual


def test_bakers_backorder_preserves_exact_offer_and_applies_to_every_variant():
    raw = item()
    raw['variants'].append({**raw['variants'][0], 'id': 2})
    product = parse(raw)
    assert all(o.availability == 'unknown' for o in product.offers)
    assert {o.availability_note for o in product.offers} == {
        'Retailer shipping notice: Machine is on backorder.'}
    offer = product.offers[0]
    assert (offer.variant_key, offer.current_price, offer.original_price, offer.options) == (
        '32158328258662', 2499, 2560, '')
    assert offer.url == BAKERS + '/products/hobart-500574?currency=USD&variant=32158328258662'


def test_bakers_independent_description_audit_withholds_confirmed_stock_only():
    raw = item()
    product = parse(raw)
    result = validate_product({'name': product.name, 'offer': asdict(product.offers[0])}, endpoint(raw), 'USD')
    assert result['status'] == 'mismatch'
    assert result['checks']['stock'] is False
    assert all(value for key, value in result['checks'].items() if key != 'stock')
    assert result['merchant']['shipping_notice'] == product.offers[0].availability_note


@pytest.mark.parametrize('origin', ['https://other.example', 'https://bakersgas.com.other.example'])
def test_bakers_description_is_source_scoped(origin):
    product = parse(item(), origin)
    assert product.offers[0].availability == 'in_stock'
    assert not product.offers[0].availability_note


def test_bakers_service_parts_promise_and_rebate_do_not_change_stock_or_prices():
    raw = item()
    raw['body_html'] = ('<p>Lincoln service parts shipping promise: backordered service parts '
                        'may qualify for expedited shipping.</p><p>$200 rebate; save more in cart.</p>')
    product = parse(raw)
    offer = product.offers[0]
    assert (offer.availability, offer.availability_note) == ('in_stock', '')
    assert (offer.current_price, offer.original_price) == (2499, 2560)
    assert validate_product({'name': product.name, 'offer': asdict(offer)}, endpoint(raw), 'USD')['status'] == 'match'


@pytest.mark.parametrize('tags', [['auto_instock', 'auto_outofstock', 'TIG Welder'],
                                 'auto_instock, AUTO_OUTOFSTOCK, TIG Welder'])
def test_cyber_negative_stock_tag_overrides_synthetic_positive_variant_and_tag(tags):
    raw = item()
    raw['body_html'] = ''
    raw['tags'] = tags
    product = parse(raw, CYBER)
    offer = product.offers[0]
    assert offer.availability == 'unknown'
    assert offer.availability_note == 'Retailer marks this product out of stock.'
    result = validate_product({'name': product.name, 'offer': asdict(offer)}, endpoint(raw), 'USD')
    assert result['checks']['stock'] is False
    assert result['merchant']['shipping_notice'] == offer.availability_note
    assert all(value for key, value in result['checks'].items() if key != 'stock')
    assert parse(raw).offers[0].availability == 'in_stock'


def test_negative_variant_is_still_excluded_and_positive_tag_still_orderable():
    raw = item()
    raw['body_html'] = ''
    raw['tags'] = ['auto_instock', 'TIG Welder']
    assert parse(raw, CYBER).offers[0].availability == 'in_stock'
    raw['variants'][0]['available'] = False
    assert ShopifyParser().parse_listing_page(json.dumps({'products': [raw]}),
                                             CYBER + '/collections/machines') == []


def test_backorder_note_and_exact_offer_survive_normalization_filters_and_daily_history(tmp_path):
    from datetime import UTC, datetime, timedelta

    from deal_common.catalog.query import query
    from deal_common.catalog.refresh import normalize
    from deal_common.catalog.storage import (
        read_offer_history,
        read_sources,
        save_source,
    )
    from tool_deals.catalog import CATALOG

    now = datetime.now(UTC)
    earlier = now - timedelta(days=1)
    raw = item()
    product = parse(raw)
    normalized = normalize([product], CATALOG, 'bakersgas.com')
    assert product.brand == 'Hobart Welding Products'
    assert normalized[0]['brand'] == 'Hobart'
    assert normalized[0]['category'] == 'Workshop equipment'
    path = tmp_path / 'welding.db'
    store = "Baker's Gas"
    save_source(path, 'tools', store, earlier.isoformat(), normalized, 'complete', {})
    filters = {'min_reference': 200, 'min_discount': 0, 'max_price': 0, 'page': 1}
    rows = read_sources(path, 'tools')
    result = query(rows, filters, now=earlier)
    selected = result['cards'][0]['offer']
    assert (selected['variant_key'], selected['current_price'], selected['original_price']) == (
        '32158328258662', 2499, 2560)
    assert selected['url'] == product.offers[0].url
    assert selected['availability'] == 'unknown'
    assert selected['availability_note'] == 'Retailer shipping notice: Machine is on backorder.'
    assert query(rows, {**filters, 'stock': True}, now=earlier)['total'] == 0

    # A new successful day can remove an absent notice without rewriting the
    # prior day's explicit stock evidence or incorporating promotional amounts.
    raw['body_html'] = '<p>$200 rebate. Free gifts and extra cart savings may apply.</p>'
    current = normalize([parse(raw)], CATALOG, 'bakersgas.com')
    save_source(path, 'tools', store, now.isoformat(), current, 'complete', {})
    rows = read_sources(path, 'tools')
    selected = query(rows, {**filters, 'stock': True}, now=now)['cards'][0]['offer']
    assert (selected['current_price'], selected['original_price'], selected['availability']) == (
        2499, 2560, 'in_stock')
    assert selected['url'] == product.offers[0].url
    history = read_offer_history(path, 'tools', store, current[0], current[0]['offers'][0], now=now)
    assert [row['availability'] for row in history] == ['in_stock', 'unknown']
    assert [row['price'] for row in history] == [2499, 2499]
    assert history[0]['availability_note'] == ''
    assert history[1]['availability_note'] == product.offers[0].availability_note
