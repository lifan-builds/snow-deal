"""Exact catalog aliases apply to old snapshots without rewriting evidence."""
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from bs4 import BeautifulSoup
from cycling_deals.catalog import CATALOG
from deal_common.catalog.identity import manufacturer_name
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.catalog.storage import (
    database,
    read_offer_history,
    read_sources,
    save_source,
)
from deal_common.catalog.web import create_app
from deal_common.config import RetailerConfig
from deal_common.models import Product
from deal_common.offers import VariantOffer
from fastapi.testclient import TestClient

ALIASES = (('acme bikes', 'ACME'), ('acme bicycles', 'ACME'), ('acme', 'ACME'))
LABELS = ('Acme Bikes', 'Acme Bicycles', 'ACME')
NOW = datetime(2026, 11, 5, 12, tzinfo=UTC)
FILTERS = {'min_discount': 0, 'min_reference': 0, 'max_price': 0, 'page': 1}


def listing(index, brand):
    url = f'https://example.com/products/bike-{index:02}'
    return {'name': f'Model {index:02}', 'url': url, 'brand': brand,
            'source_category': 'Mountain Bikes', 'category': 'Mountain bikes', 'format': '', 'platform': '',
            'offers': [
                {'variant_key': f'{index}-small', 'url': url + f'?variant={index}-small',
                 'current_price': 100, 'original_price': 4000, 'size': 'S', 'options': 'S / Blue',
                 'availability': 'in_stock', 'image_url': None, 'availability_note': ''},
                {'variant_key': f'{index}-medium', 'url': url + f'?variant={index}-medium',
                 'current_price': 1500 + 10 * index, 'original_price': 4000, 'size': 'M', 'options': 'M / Red',
                 'availability': 'in_stock', 'image_url': None, 'availability_note': ''},
            ]}


def rows(now=NOW):
    products = [listing(i, LABELS[i % 3]) for i in range(35)]
    products += [listing(40, 'ACME Components'), listing(41, 'Acme Bicycle'), listing(42, 'In Stock')]
    return [{'name': name, 'successful_at': now.isoformat(), 'products': products[offset::2]}
            for offset, name in enumerate(('One', 'Two'))]


def pages(sources, filters, **kwargs):
    first = query(sources, filters, **kwargs)
    cards = list(first['cards'])
    for page in range(2, first['pages'] + 1):
        cards += query(sources, {**filters, 'page': page}, **kwargs)['cards']
    return first, cards


@pytest.mark.parametrize(('raw', 'expected'), [
    ('Acme Bikes', 'ACME'), (' ACME BICYCLES ', 'ACME'), ('ACME', 'ACME'),
    ('ACME Components', 'ACME Components'), ('Acme Bicycle', 'Acme Bicycle'),
    ('Other <Maker>', 'Other <Maker>'), (None, 'Unspecified'), ('', 'Unspecified'),
    ('ESD：Nov.30（Black）', 'Unspecified'), ('In Stock', 'Unspecified'),
])
def test_manufacturer_identity_uses_only_explicit_aliases_after_fulfillment_cleanup(raw, expected):
    assert manufacturer_name(raw, brand_aliases=ALIASES) == expected
    assert manufacturer_name(raw) == manufacturer_name(raw, brand_aliases=())
    assert manufacturer_name('In Stock', brand_aliases=(('in stock', 'ACME'),)) == 'Unspecified'


@pytest.mark.parametrize('requested', ['ACME', 'Acme Bikes', 'Acme Bicycles', 'ACME BIKES'])
def test_alias_filter_unites_full_group_before_count_page_and_exact_offer_selection(requested):
    sources = rows()
    original = deepcopy(sources)
    filters = {**FILTERS, 'brand': requested, 'size': 'M', 'stock': True}
    first, cards = pages(sources, filters, now=NOW, brand_aliases=ALIASES)
    assert first['total'] == 35 and first['pages'] == 2
    assert len(first['cards']) == 24
    assert len(query(sources, filters, now=NOW, brand_aliases=ALIASES)['cards']) == 24
    assert len(query(sources, {**filters, 'page': 2}, now=NOW, brand_aliases=ALIASES)['cards']) == 11
    assert [p['name'] for p in cards] == [f'Model {i:02}' for i in range(35)]
    assert {p['brand'] for p in cards} == {'ACME'}
    assert first['facets']['brand'] == ['ACME', 'ACME Components', 'Acme Bicycle', 'Unspecified']
    for index, card in enumerate(cards):
        offer = card['offer']
        assert (offer['variant_key'], offer['current_price'], offer['original_price'],
                offer['size'], offer['options'], offer['availability'], offer['availability_note']) == (
                    f'{index}-medium', 1500 + 10 * index, 4000, 'M', 'M / Red', 'in_stock', '')
        assert offer['url'] == card['url'] + f'?variant={index}-medium'
    assert sources == original and filters['brand'] == requested
    _, reversed_cards = pages(list(reversed(sources)), filters, now=NOW, brand_aliases=ALIASES)
    assert reversed_cards == cards
    budget = query(sources, {**filters, 'max_price': 1540}, now=NOW, brand_aliases=ALIASES)
    assert budget['total'] == 5


def test_unrestricted_order_and_no_alias_calls_stay_unchanged_and_raw_brand_search_survives():
    sources = rows()
    original = deepcopy(sources)
    before, old_cards = pages(sources, FILTERS, now=NOW)
    after, new_cards = pages(sources, FILTERS, now=NOW, brand_aliases=ALIASES)
    assert (before['total'], before['pages']) == (after['total'], after['pages'])
    assert [{k: v for k, v in c.items() if k != 'brand'} for c in old_cards] == [
        {k: v for k, v in c.items() if k != 'brand'} for c in new_cards]
    assert query(sources, {**FILTERS, 'brand': 'Acme Bikes'}, now=NOW)['total'] == 12
    assert query(sources, {**FILTERS, 'brand': 'In Stock'}, now=NOW)['total'] == 1
    assert query(sources, {**FILTERS, 'q': 'ACME ACME'}, now=NOW)['total'] == 0
    assert query(sources, {**FILTERS, 'brand': 'ACME Components'}, now=NOW, brand_aliases=ALIASES)['total'] == 1
    raw_search = query(sources, {**FILTERS, 'q': 'bicycles'}, now=NOW, brand_aliases=ALIASES)
    assert raw_search['total'] == 12 and {c['brand'] for c in raw_search['cards']} == {'ACME'}
    assert sources == original


def app_with_rows(tmp_path):
    sources = rows(datetime.now(UTC))
    config = replace(CATALOG, brand_aliases=ALIASES,
                     sources=tuple(RetailerConfig(row['name'], 'example.com', ['https://example.com/collection'])
                                   for row in sources))
    path = tmp_path / 'catalog.db'
    for row in sources:
        save_source(path, config.slug, row['name'], row['successful_at'], row['products'], 'complete', {})
    return TestClient(create_app(config, path)), path


def test_legacy_brand_urls_select_canonical_label_and_generate_canonical_pagination(tmp_path):
    client, path = app_with_rows(tmp_path)
    original = path.read_bytes()
    health = client.get('/healthz').json()
    response = client.get('/', params={'brand': 'Acme Bikes', 'size': 'M', 'stock': 'true', 'min_reference': 0})
    html = BeautifulSoup(response.text, 'html.parser')
    assert html.select_one('select[name="brand"] option[selected]').text == 'ACME'
    assert html.select_one('a[aria-label="Remove filter: Brand: ACME"]')
    assert {p.text for p in html.select('.product-brand')} == {'ACME'}
    links = [a['href'] for a in html.select('a') if parse_qs(urlsplit(a.get('href', '')).query).get('page') == ['2']]
    assert links
    for link in links:
        params = parse_qs(urlsplit(link).query)
        assert params['brand'] == ['ACME'] and params['size'] == ['M'] and params['stock'] == ['true']
    page_two = BeautifulSoup(client.get(links[0]).text, 'html.parser')
    assert len(page_two.select('.product-brand')) == 11
    assert health == client.get('/healthz').json() and path.read_bytes() == original


def test_unknown_brand_stays_selected_escaped_and_distinct_in_legacy_form(tmp_path):
    client, _ = app_with_rows(tmp_path)
    value = '<Unknown "maker"> & ACME'
    response = client.get('/', params={'brand': value})
    html = BeautifulSoup(response.text, 'html.parser')
    assert html.select_one('select[name="brand"] option[selected]').text == value
    assert value not in response.text
    assert html.select_one('.results-bar strong').text == '0'
    assert not html.select('.product-brand')


def test_alias_history_survives_next_ingestion_without_joining_other_manufacturer(tmp_path):
    path = tmp_path / 'history.db'
    old = listing(0, 'Acme Bikes')
    legacy = listing(0, 'Acme Bicycles')
    unrelated = listing(0, 'ACME Components')
    old['offers'][1].update(current_price=1800, availability='unknown', availability_note='Merchant shipping estimate')
    legacy['offers'][1]['current_price'] = 1700
    for days, row in [(3, old), (2, unrelated), (1, legacy)]:
        save_source(path, 'cycling', 'One', (NOW - timedelta(days=days)).isoformat(), [row], 'complete', {})
    original = path.read_bytes()
    history = read_offer_history(path, 'cycling', 'One', legacy, legacy['offers'][1], now=NOW,
                                 brand_aliases=ALIASES)
    assert [r['price'] for r in history] == [1700, 1800]
    assert history[1]['availability'] == 'unknown' and history[1]['availability_note'] == 'Merchant shipping estimate'
    assert path.read_bytes() == original
    catalog = replace(CATALOG, brand_aliases=ALIASES)
    product = Product(legacy['name'], legacy['url'], 1500, 4000, brand='Acme Bikes',
                      product_type='Mountain Bikes', offers=[VariantOffer(**o) for o in listing(0, 'Acme Bikes')['offers']])
    current = normalize([product], catalog, 'example.com')[0]
    assert current['brand'] == 'ACME' and product.brand == 'Acme Bikes'
    save_source(path, 'cycling', 'One', NOW.isoformat(), [current], 'complete', {})
    original = path.read_bytes()
    selected = current['offers'][1]
    history = read_offer_history(path, 'cycling', 'One', current, selected, now=NOW, brand_aliases=ALIASES)
    assert [r['price'] for r in history] == [1500, 1700, 1800]
    assert len(read_offer_history(path, 'cycling', 'One', current, selected, now=NOW)) == 1
    assert path.read_bytes() == original
    with database(path, 'cycling') as connection:
        historical_text = [r[0] for r in connection.execute('SELECT products FROM observations')]
    assert any('Acme Bikes' in text for text in historical_text)
    assert any('Acme Bicycles' in text for text in historical_text)
    assert read_sources(path, 'cycling')[0]['successful_at'] == NOW.isoformat()


@pytest.mark.parametrize(('level', 'field', 'value'), [
    ('product', 'brand', 'ACME Components'), ('product', 'name', 'Different build'),
    ('product', 'url', 'https://example.com/products/different'),
    ('offer', 'variant_key', 'different'), ('offer', 'options', 'Different package'),
    ('offer', 'url', 'https://example.com/products/bike-00?variant=different'),
])
def test_brand_aliases_preserve_every_other_exact_history_identity_guard(tmp_path, level, field, value):
    path = tmp_path / 'history.db'
    previous = listing(0, 'Acme Bikes')
    current = listing(0, 'ACME')
    (previous if level == 'product' else previous['offers'][1])[field] = value
    save_source(path, 'cycling', 'One', NOW.isoformat(), [previous], 'complete', {})
    assert read_offer_history(path, 'cycling', 'One', current, current['offers'][1],
                              now=NOW, brand_aliases=ALIASES) == []
    assert read_offer_history(path, 'cycling', 'Other store', current, current['offers'][1],
                              now=NOW, brand_aliases=ALIASES) == []


def test_history_route_uses_catalog_aliases_for_current_legacy_brand(tmp_path):
    client, path = app_with_rows(tmp_path)
    now = datetime.now(UTC)
    old = listing(0, 'Acme Bicycles')
    save_source(path, 'cycling', 'One', (now - timedelta(days=1)).isoformat(), [old], 'complete', {})
    current = listing(0, 'ACME')
    save_source(path, 'cycling', 'One', now.isoformat(), [current], 'complete', {})
    original = path.read_bytes()
    response = client.get('/history', params={'source': 'One', 'product': current['url'], 'variant': '0-medium'})
    assert response.status_code == 200 and '2 observed days' in response.text
    assert path.read_bytes() == original
