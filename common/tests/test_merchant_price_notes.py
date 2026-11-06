"""Price caveats travel with exact offers and their own dated observations."""
import json
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from cycling_deals.catalog import CATALOG
from deal_common.catalog.audit import validate_product
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.catalog.storage import read_offer_history, read_sources, save_source
from deal_common.catalog.web import create_app
from deal_common.config import RetailerConfig
from deal_common.offers import VariantOffer
from deal_common.parsers.shopify import ShopifyParser, pricing_notice
from fastapi.testclient import TestClient

ORIGIN = 'https://contenderbicycles.com'
NOTE = 'Retailer asks you to contact them for current pricing.'
TAG = 'contact-for-current-price'


def item():
    payload = json.loads((Path(__file__).parent / 'fixtures/contender_generated_options.json').read_text())
    raw = next(p for p in payload['products'] if p['handle'] == 'open-up-rapha-frameset')
    raw['variants'] = [v for v in raw['variants'] if v['id'] == 43266977104117]
    return raw


def parse(raw, origin=ORIGIN):
    return ShopifyParser(size_option_names=CATALOG.size_option_names,
                         size_value_pattern=CATALOG.size_value_pattern).parse_listing_page(
                             json.dumps({'products': [raw]}), origin + '/collections/sale?currency=USD')


def endpoint(raw):
    result = deepcopy(raw)
    for variant in result['variants']:
        for field in ('price', 'compare_at_price'):
            variant[field] = int(Decimal(str(variant[field])) * 100)
        variant['options'] = [variant[k] for k in ('option1', 'option2', 'option3') if variant.get(k)]
    return result


def no_notes(value):
    if isinstance(value, dict):
        return {k: no_notes(v) for k, v in value.items() if k != 'price_note'}
    if isinstance(value, list):
        return [no_notes(v) for v in value]
    return value


@pytest.mark.parametrize('tags', [[TAG], ['Frameset', TAG], 'Frameset, contact-for-current-price',
                                 ' contact-for-current-price '])
@pytest.mark.parametrize('origin', [ORIGIN, 'https://www.contenderbicycles.com'])
def test_exact_tag_list_or_string_adds_fixed_note_and_changes_no_other_offer_fact(tags, origin):
    raw = item()
    raw['tags'] = tags
    original = deepcopy(raw)
    noted = parse(raw, origin)[0]
    plain = parse({**raw, 'tags': []}, origin)[0]
    plain.tags = noted.tags  # The input tags differ; preserve and compare all other facts.
    # Compare all Product/offer facts after removing only the new metadata field.
    assert no_notes(asdict(noted)) == no_notes(asdict(plain))
    offer = noted.offers[0]
    assert offer.price_note == NOTE
    assert (offer.variant_key, offer.current_price, offer.original_price, offer.availability, offer.size) == (
        '43266977104117', 1799, 3400, 'in_stock', 'XL')
    assert offer.options == 'Rapha Limited Edition / XL'
    assert offer.url == origin + '/products/open-up-rapha-frameset?currency=USD&variant=43266977104117'
    assert not offer.availability_note and raw == original


@pytest.mark.parametrize('tags', [[], None, 'contact-for-current-price-extra', 'CONTACT-FOR-CURRENT-PRICE',
                                 'contact_for_current_price', 'contact-for-price', ['Other', 1, None]])
def test_unrelated_tags_and_description_words_do_not_create_price_notes(tags):
    raw = {**item(), 'tags': tags, 'body_html': '<p>Contact us for current price</p>'}
    assert pricing_notice(raw, ORIGIN) == ''
    assert parse(raw)[0].offers[0].price_note == ''


@pytest.mark.parametrize('origin', ['https://other.example', 'https://contenderbicycles.com.other.example'])
def test_other_hosts_do_not_inherit_contender_tag_semantics(origin):
    raw = {**item(), 'tags': [TAG]}
    assert pricing_notice(raw, origin) == ''
    assert parse(raw, origin)[0].offers[0].price_note == ''


@pytest.mark.parametrize(('available', 'expected'), [(True, 'in_stock'), (None, 'unknown'), (False, None)])
def test_price_note_neither_downgrades_nor_promotes_stock(available, expected):
    raw = item()
    raw['variants'][0]['available'] = available
    noted = parse({**raw, 'tags': [TAG]})
    plain = parse({**raw, 'tags': []})
    for with_note, without_note in zip(noted, plain, strict=True):
        without_note.tags = with_note.tags
    assert no_notes([asdict(p) for p in noted]) == no_notes([asdict(p) for p in plain])
    if expected is None:
        assert noted == []
    else:
        assert noted[0].offers[0].availability == expected
        assert noted[0].offers[0].price_note == NOTE


def test_notes_do_not_change_query_population_ranking_pagination_fit_or_selected_offer():
    raw_products = []
    for index in range(30):
        raw = item()
        raw.update(handle=f'frame-{index:02}', title=f'Frameset {index:02}', tags=[TAG] if index % 2 else [])
        raw['variants'][0].update(id=1000 + index, price=str(1500 + index))
        raw_products.append(raw)
    now = datetime.now(UTC)
    def rows(products):
        parsed = ShopifyParser(size_option_names=CATALOG.size_option_names).parse_listing_page(
            json.dumps({'products': products}), ORIGIN + '/collections/sale?currency=USD')
        return [{'name': 'Contender', 'successful_at': now.isoformat(),
                 'products': normalize(parsed, CATALOG, 'contenderbicycles.com')}]
    tagged = rows(raw_products)
    plain = rows([{**p, 'tags': []} for p in raw_products])
    original = deepcopy(tagged)
    for filters in [{'size': 'XL'}, {'stock': True}, {'max_price': 1510}, {'min_discount': 55}]:
        base = {'min_reference': 1000, 'max_price': 0, 'min_discount': 0, 'page': 1, **filters}
        for page in (1, 2):
            noted = query(tagged, {**base, 'page': page}, now=now)
            before = query(plain, {**base, 'page': page}, now=now)
            assert no_notes(noted) == no_notes(before)
    assert tagged == original


@pytest.mark.parametrize('endpoint_tags', [[TAG], 'Frameset,contact-for-current-price'])
def test_independent_audit_compares_current_note_without_changing_price_or_stock_checks(endpoint_tags):
    raw = item()
    p = parse(raw)[0]
    card = {'name': p.name, 'offer': asdict(p.offers[0])}
    actual = endpoint(raw)
    actual['tags'] = endpoint_tags
    result = validate_product(card, actual, 'USD')
    assert result['status'] == 'match' and result['checks']['price_note'] is True
    assert result['merchant']['price_note'] == NOTE
    assert all(result['checks'].values())
    for expected in (None, 'Changed note'):
        wrong = deepcopy(card)
        if expected is None:
            wrong['offer'].pop('price_note')
        else:
            wrong['offer']['price_note'] = expected
        rejected = validate_product(wrong, actual, 'USD')
        assert rejected['status'] == 'mismatch' and rejected['checks']['price_note'] is False
        assert all(value for key, value in rejected['checks'].items() if key != 'price_note')
    actual['tags'] = []
    rejected = validate_product(card, actual, 'USD')
    assert rejected['status'] == 'mismatch' and rejected['merchant']['price_note'] == ''


def test_audits_without_current_or_stored_note_keep_legacy_result_shape():
    raw = {**item(), 'tags': []}
    p = parse(raw)[0]
    offer = asdict(p.offers[0])
    offer.pop('price_note')
    result = validate_product({'name': p.name, 'offer': offer}, endpoint(raw), 'USD')
    assert result['status'] == 'match'
    assert set(result['checks']) == {'identity', 'currency', 'price', 'reference', 'options', 'stock'}
    assert 'price_note' not in result['merchant']


def test_legacy_offer_constructor_keeps_empty_optional_note():
    p = parse(item())[0]
    legacy = asdict(p.offers[0])
    legacy.pop('price_note')
    assert VariantOffer(**legacy).price_note == ''


def test_card_details_and_dated_history_escape_selected_note_without_backfilling_legacy(tmp_path):
    raw = item()
    raw['variants'].append({**raw['variants'][0], 'id': 123, 'option2': 'M', 'price': '1499.00'})
    product = normalize(parse(raw), CATALOG, 'contenderbicycles.com')[0]
    selected = next(o for o in product['offers'] if o['variant_key'] == '43266977104117')
    other = next(o for o in product['offers'] if o['variant_key'] == '123')
    selected['price_note'] = '<script>selected XL</script> & current'
    other['price_note'] = 'Other variant caveat'
    catalog = replace(CATALOG, sources=(RetailerConfig('Contender', 'contenderbicycles.com', [ORIGIN + '/collections/sale']),))
    path = tmp_path / 'catalog.db'
    now = datetime.now(UTC)
    old = deepcopy(product)
    for offer in old['offers']:
        offer['price_note'] = '<b>Historical only</b>'
    save_source(path, 'cycling', 'Contender', (now - timedelta(days=2)).isoformat(), [old], 'complete', {})
    legacy = deepcopy(product)
    for offer in legacy['offers']:
        offer.pop('price_note')
    save_source(path, 'cycling', 'Contender', (now - timedelta(days=1)).isoformat(), [legacy], 'complete', {})
    save_source(path, 'cycling', 'Contender', now.isoformat(), [product], 'complete', {})
    original_bytes = path.read_bytes()
    history = read_offer_history(path, 'cycling', 'Contender', product, selected, now=now)
    assert [row['price_note'] for row in history] == [selected['price_note'], '', '<b>Historical only</b>']
    assert read_sources(path, 'cycling')[0]['successful_at'] == now.isoformat()
    with TestClient(create_app(catalog, path)) as client:
        page = client.get('/', params={'size': 'XL'})
        soup = BeautifulSoup(page.text, 'html.parser')
        notes = soup.select('article .price-note')
        assert len(notes) == 2 and {p.get_text() for p in notes} == {selected['price_note']}
        assert selected['price_note'] not in page.text and other['price_note'] not in page.text
        assert 'Reported in stock' in page.text and '$1,799' in page.text
        history_page = client.get(soup.select_one('a.history-link')['href'])
        history_soup = BeautifulSoup(history_page.text, 'html.parser')
        rows = history_soup.select('tbody tr')
        assert len(rows) == 3
        assert rows[0].select_one('.price-note').get_text() == selected['price_note']
        assert rows[1].select_one('.price-note') is None
        assert rows[2].select_one('.price-note').get_text() == '<b>Historical only</b>'
        assert selected['price_note'] not in history_page.text and '<b>Historical only</b>' not in history_page.text
    assert path.read_bytes() == original_bytes


def test_legacy_snapshot_without_note_renders_no_empty_or_current_price_notice(tmp_path):
    p = normalize(parse(item()), CATALOG, 'contenderbicycles.com')[0]
    for offer in p['offers']:
        offer.pop('price_note')
    path = tmp_path / 'legacy.db'
    now = datetime.now(UTC)
    save_source(path, 'cycling', 'Contender Bicycles', now.isoformat(), [p], 'complete', {})
    with TestClient(create_app(CATALOG, path)) as client:
        page = client.get('/')
        assert page.status_code == 200 and not BeautifulSoup(page.text, 'html.parser').select('.price-note')
