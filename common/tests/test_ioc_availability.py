"""Captured IOC made-to-order notices override positive variant availability."""
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from deal_common.catalog.audit import validate_product
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.catalog.storage import read_offer_history, read_sources, save_source
from deal_common.parsers.shopify import ShopifyParser
from tool_deals.catalog import CATALOG

ORIGIN = 'https://www.weldingsuppliesfromioc.com'


def captured():
    return json.loads((Path(__file__).parent / 'fixtures/ioc_made_to_order.json').read_text())['products']


def parse(raw, origin=ORIGIN):
    return ShopifyParser().parse_listing_page(json.dumps({'products': [raw]}),
                                             origin + '/collections/all-welders?currency=USD')[0]


def endpoint(raw):
    response = deepcopy(raw)
    response['description'] = response.pop('body_html')
    for variant in response['variants']:
        variant['options'] = [variant[key] for key in ('option1', 'option2', 'option3') if variant.get(key)]
        for key in ('price', 'compare_at_price'):
            variant[key] = int(Decimal(str(variant[key])) * 100)
    return response


@pytest.mark.parametrize('raw', captured(), ids=lambda raw: raw['handle'])
def test_each_captured_active_notice_preserves_exact_offer_and_withholds_stock(raw):
    original = deepcopy(raw)
    assert all(variant['available'] is True for variant in raw['variants'])
    observed = parse(raw)
    ordinary = parse({**raw, 'body_html': ''})
    notice = 'Retailer shipping notice: ' + BeautifulSoup(raw['body_html'], 'html.parser').get_text(' ', strip=True)
    assert len(observed.offers) == len(ordinary.offers)
    for actual, baseline in zip(observed.offers, ordinary.offers, strict=True):
        assert actual.availability == 'unknown' and actual.availability_note == notice
        assert baseline.availability == 'in_stock'
        assert asdict(actual) == {**asdict(baseline), 'availability': 'unknown', 'availability_note': notice}
    assert raw == original


@pytest.mark.parametrize('raw', captured(), ids=lambda raw: raw['handle'])
def test_separate_product_description_audit_rejects_only_stock_confirmation(raw):
    product = parse(raw)
    offer = product.offers[0]
    result = validate_product({'name': product.name, 'offer': asdict(offer)}, endpoint(raw), 'USD')
    assert result['status'] == 'mismatch'
    assert result['checks']['stock'] is False
    assert all(value for key, value in result['checks'].items() if key != 'stock')
    assert result['merchant']['shipping_notice'] == offer.availability_note


@pytest.mark.parametrize('origin', ['https://other.example', 'https://www.weldingsuppliesfromioc.com.other.example'])
def test_ioc_made_to_order_notice_is_source_scoped(origin):
    offer = parse(captured()[-1], origin).offers[0]
    assert (offer.availability, offer.availability_note) == ('in_stock', '')


@pytest.mark.parametrize('body', [
    '<p>Some machines are made-to-order. Please allow extra shipping time.</p>',
    '<p>These service parts are made-to-order from Miller. Please allow 2-3 weeks for shipment.</p>',
    '<p>These generators were made-to-order from Miller. Please allow 2-3 weeks for shipment.</p>',
    '<p>These machines are not made-to-order from Lincoln. Please allow 4-6 weeks for shipping.</p>',
    '<p>If these packages are made-to-order from Miller. Please expect a 2-3 week lead time.</p>',
    '<p>FAQ: Are these generators made-to-order from Miller? Please contact us for shipment.</p>',
    '<p>These generators are in stock. $500 rebate and free accessories may apply.</p>',
    '<script>These packages are made-to-order from Miller. Please expect a 2-3 week lead time.</script>',
    '<template>These generators are Made-to-Order from Miller. Please allow 1-2 weeks for your order to ship.</template>',
])
def test_generic_service_historical_hypothetical_and_inactive_text_do_not_change_stock(body):
    raw = {**captured()[-1], 'body_html': body}
    product = parse(raw)
    offer = product.offers[0]
    assert (offer.availability, offer.availability_note) == ('in_stock', '')
    assert (offer.current_price, offer.original_price) == (21348, 24655)
    assert validate_product({'name': product.name, 'offer': asdict(offer)}, endpoint(raw), 'USD')['status'] == 'match'


def test_made_to_order_cannot_restore_an_explicitly_unavailable_variant():
    raw = captured()[-1]
    raw['variants'][0]['available'] = False
    assert ShopifyParser().parse_listing_page(json.dumps({'products': [raw]}),
                                             ORIGIN + '/collections/all-welders?currency=USD') == []


def test_made_to_order_note_survives_query_and_keeps_previous_daily_evidence_exact(tmp_path):
    raw = captured()[-1]
    now = datetime.now(UTC)
    earlier = now - timedelta(days=1)
    ordinary = normalize([parse({**raw, 'body_html': ''})], CATALOG, 'www.weldingsuppliesfromioc.com')
    current = normalize([parse(raw)], CATALOG, 'www.weldingsuppliesfromioc.com')
    assert len(current) == len(ordinary) == 1
    store = 'Welding Supplies from IOC'
    path = tmp_path / 'ioc-history.db'
    save_source(path, 'tools', store, earlier.isoformat(), ordinary, 'complete', {})
    earlier_history = read_offer_history(path, 'tools', store, ordinary[0], ordinary[0]['offers'][0], now=earlier)
    save_source(path, 'tools', store, now.isoformat(), current, 'complete', {})
    sources = read_sources(path, 'tools')
    filters = {'min_reference': 200, 'min_discount': 0, 'max_price': 0, 'page': 1}
    selected = query(sources, filters, now=now)['cards'][0]['offer']
    expected = current[0]['offers'][0]
    assert expected.items() <= selected.items()
    assert selected['availability'] == 'unknown'
    assert query(sources, {**filters, 'stock': True}, now=now)['total'] == 0
    history = read_offer_history(path, 'tools', store, current[0], expected, now=now)
    assert history[1:] == earlier_history
    assert [row['availability'] for row in history] == ['unknown', 'in_stock']
    assert [row['price'] for row in history] == [21348, 21348]
    assert history[0]['availability_note'] == expected['availability_note']
    assert history[1]['availability_note'] == ''
