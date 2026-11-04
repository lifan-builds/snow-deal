import asyncio
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup
from cycling_deals.catalog import CATALOG
from deal_common.catalog.query import query
from deal_common.catalog.refresh import refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.parsers.racycles import RacyclesShopifyParser, detail_data

FIXTURES = Path(__file__).parent / 'fixtures'
HTML = (FIXTURES / 'racycles-purchase.html').read_text()
RAW = json.loads((FIXTURES / 'racycles-product.json').read_text())
URL = 'https://racycles.com/products/' + RAW['handle']
COLLECTION = 'https://racycles.com/collections/bikes?currency=USD'
KEY = '44030761173036'


def feed(raw=RAW):
    item = deepcopy(raw)
    item['product_type'] = item.pop('type')
    item['images'] = [{'src': 'https://racycles.com/cdn/shop/files/example.jpg', 'variant_ids': []}]
    for variant in item['variants']:
        variant['price'] = f"{variant['price'] / 100:.2f}"
        variant['compare_at_price'] = f"{variant['compare_at_price'] / 100:.2f}" if variant['compare_at_price'] else None
    return json.dumps({'products': [item]})


def parser(raw=RAW):
    p = RacyclesShopifyParser(size_option_names=CATALOG.size_option_names,
                             size_value_pattern=CATALOG.size_value_pattern)
    p.parse_listing_page(feed(raw), COLLECTION)
    return p


def parse(html=HTML, raw=RAW):
    return parser(raw).parse_product_evidence(html, URL + '?currency=USD', json.dumps(raw))


def change(html=HTML, *, status=None, group=None, selected=None):
    soup = BeautifulSoup(html, 'html.parser')
    if status:
        node = soup.select_one('script.variant-status-map')
        value = json.loads(node.string)
        status(value)
        node.string = json.dumps(value)
    if group:
        for node in soup.select('script[type="application/ld+json"]'):
            value = json.loads(node.string)
            if value['@type'] == 'ProductGroup':
                group(value)
                node.string = json.dumps(value)
    if selected:
        node = soup.select_one('variant-picker script[type="application/json"]')
        value = json.loads(node.string)
        selected(value)
        node.string = json.dumps(value)
    return str(soup)


def test_exact_variants_and_final_sale_disclosure_preserved():
    products = parse()
    assert len(products) == 1
    product = products[0]
    offer = product.offers[0]
    assert product.name == RAW['title'] and product.brand == '3T'
    assert (offer.variant_key, offer.current_price, offer.original_price, offer.size) == (KEY, 2799.99, 5999, '61cm')
    assert offer.options == 'Red / White / 61cm' and offer.availability == 'in_stock'
    assert 'Final Sale' in offer.availability_note and 'cannot be returned or exchanged' in offer.availability_note
    assert offer.url == URL + '?currency=USD&variant=' + KEY
    p = parser()
    assert p.get_product_evidence_url(HTML, URL) == URL + '.js?currency=USD'
    with pytest.raises(ValueError, match='endpoint evidence required'):
        p.parse_product_page(HTML, URL)


def test_virtual_warehouse_overrides_available_without_copying_hidden_immediate_message():
    html = change(status=lambda status: status[KEY].update(vw=True))
    soup = BeautifulSoup(html, 'html.parser')
    soup.select_one('.in-stock-message--immediate')['hidden'] = ''
    del soup.select_one('.in-stock-message--vw')['hidden']
    product = parse(str(soup))[0]
    assert product.offers[0].availability == 'unknown'
    assert '1-2 weeks' in product.offers[0].availability_note
    assert 'Final Sale' in product.offers[0].availability_note


def test_preorder_available_with_zero_quantity_never_confirms_stock():
    html = change(status=lambda status: status[KEY].update(qty=0))
    soup = BeautifulSoup(html, 'html.parser')
    soup.select_one('.in-stock-message--immediate')['hidden'] = ''
    soup.select_one('div.product-info').append(BeautifulSoup(
        '<div class="product-backorder"><div class="backorder"><div class="custom-backorder-message">'
        'Coming soon! A sales associate will contact you with the shipping date.'
        '</div></div></div>', 'html.parser'))
    offer = parse(str(soup))[0].offers[0]
    assert offer.availability == 'unknown' and 'Coming soon!' in offer.availability_note
    with pytest.raises(ValueError, match='backorder evidence'):
        parse(html)


def test_explicit_unavailable_detail_excludes_offer_even_when_feed_remains_available():
    raw = deepcopy(RAW)
    raw['variants'][5]['available'] = False
    html = change(status=lambda status: status[KEY].update(qty=0, available=False),
                  selected=lambda selected: selected.update(available=False),
                  group=lambda group: group['hasVariant'][5]['offers'].update(availability='https://schema.org/OutOfStock'))
    soup = BeautifulSoup(html, 'html.parser')
    soup.select_one('.in-stock-message--immediate')['hidden'] = ''
    del soup.select_one('.in-stock-message--soldout')['hidden']
    assert parser().parse_product_evidence(str(soup), URL + '?currency=USD', json.dumps(raw)) == []


def two_discounted(*, selected_full_price=False):
    raw = deepcopy(RAW)
    first = raw['variants'][0]
    first.update(price=100000, compare_at_price=1000000, available=True)
    if selected_full_price:
        raw['variants'][5]['compare_at_price'] = None
    def group(value):
        value['hasVariant'][0]['offers'].update(price='1000.00', availability='https://schema.org/InStock')
    html = change(status=lambda status: status[str(first['id'])].update(qty=1, available=True), group=group)
    if selected_full_price:
        html = change(html, selected=lambda selected: selected.update(compare_at_price=None))
        soup = BeautifulSoup(html, 'html.parser')
        soup.select_one('.price__was').decompose()
        html = str(soup)
    return raw, html


def test_multiple_discount_prices_remain_bound_to_each_exact_size():
    raw, html = two_discounted()
    offers = parse(html, raw)[0].offers
    assert [(o.variant_key, o.current_price, o.original_price, o.size) for o in offers] == [
        ('44030761631788', 1000, 10000, 'XXS'), (KEY, 2799.99, 5999, '61cm')]
    assert parse(html, raw)[0].current_price == 1000


def test_selected_full_price_variant_does_not_hide_another_discounted_variant():
    raw, html = two_discounted(selected_full_price=True)
    product = parse(html, raw)[0]
    assert [(o.variant_key, o.current_price, o.original_price) for o in product.offers] == [('44030761631788', 1000, 10000)]


@pytest.mark.parametrize('mutation', [
    lambda status: status.pop(KEY),
    lambda status: status.update({'999': {'qty': 1, 'vw': False, 'available': True}}),
    lambda status: status[KEY].update(qty=True),
    lambda status: status[KEY].update(qty=float('nan')),
    lambda status: status[KEY].update(vw='false'),
    lambda status: status[KEY].update(available=1),
    lambda status: status[KEY].update(available=False),
])
def test_missing_ambiguous_or_conflicting_stock_cannot_complete(mutation):
    with pytest.raises((ValueError, TypeError)):
        parse(change(status=mutation))


@pytest.mark.parametrize('mutation', [
    lambda raw: raw.update(id=123),
    lambda raw: raw.update(handle='other'),
    lambda raw: raw['variants'].pop(),
    lambda raw: raw['variants'].append(raw['variants'][0]),
    lambda raw: raw['variants'][5].update(price=1),
    lambda raw: raw['variants'][5].update(compare_at_price=600000),
    lambda raw: raw['variants'][5].update(options=['Wrong', '61cm']),
    lambda raw: raw['variants'][5].update(quantity_rule={'min': 2, 'increment': 1}),
])
def test_endpoint_identity_price_reference_and_options_must_agree(mutation):
    raw = deepcopy(RAW)
    mutation(raw)
    with pytest.raises((ValueError, TypeError)):
        parser().parse_product_evidence(HTML, URL + '?currency=USD', json.dumps(raw))


@pytest.mark.parametrize(('before', 'after'), [
    ('"priceCurrency": "USD"', '"priceCurrency": "CAD"'),
    ('<sup>99</sup>', '<sup>98</sup>'),
    ('value="' + KEY + '"', 'value="999"'),
    ('checked=""', ''),
    ('data-option="Size"', 'data-option="Wheel Size"'),
    ('https://racycles.com/products/', 'https://evil.example/products/'),
])
def test_displayed_identity_currency_options_and_cents_are_not_assumed(before, after):
    assert before in HTML
    with pytest.raises((ValueError, TypeError)):
        parse(HTML.replace(before, after))


def test_wrong_requested_variant_and_duplicate_stock_key_are_rejected():
    with pytest.raises(ValueError, match='requested variant'):
        detail_data(HTML, URL + '?variant=999', RAW)
    soup = BeautifulSoup(HTML, 'html.parser')
    node = soup.select_one('script.variant-status-map')
    node.string = '{"' + KEY + '":{},"' + KEY + '":{}}'
    with pytest.raises(ValueError, match='Duplicate RA JSON key'):
        parse(str(soup))


def test_paced_detail_and_endpoint_failures_preserve_last_complete_snapshot(tmp_path):
    source = RetailerConfig('RA Cycles', 'racycles.com', [COLLECTION], verify_shopify_currency=True)
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'cycling.db'
    seen = []
    def handler(request):
        seen.append(str(request.url))
        if request.url.path.startswith('/collections/'):
            if request.url.path.endswith('.json'):
                return httpx.Response(200, text=feed())
            return httpx.Response(200, text='<script>Shopify.currency = {"active":"USD"};</script>')
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json=RAW)
        return httpx.Response(200, text=HTML)
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]['status'] == 'complete'
    assert report[0]['product_pages'] == report[0]['evidence_requests'] == 1
    assert len(seen) == 4 and seen[-1] == URL + '.js?currency=USD'
    before = read_sources(path, 'cycling')[0]
    filters = {'min_reference': 1000, 'min_discount': 40, 'max_price': 0, 'stock': True, 'page': 1}
    assert query([before], filters)['total'] == 1
    def failed(request):
        if request.url.path.endswith('.js'):
            return httpx.Response(200, json={})
        return handler(request)
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(failed)))
    assert report[0]['status'] == 'incomplete'
    after = read_sources(path, 'cycling')[0]
    assert after['successful_at'] == before['successful_at']
    assert after['products'] == before['products']


def test_virtual_warehouse_notice_tracks_actual_merchant_template():
    html = change(status=lambda status: status[KEY].update(vw=True))
    soup = BeautifulSoup(html, 'html.parser')
    soup.select_one('.in-stock-message--immediate')['hidden'] = ''
    node = soup.select_one('.in-stock-message--vw')
    del node['hidden']
    node.string = 'In Stock Ships in 3-4 weeks based on its location'
    note = parse(str(soup))[0].offers[0].availability_note
    assert '3-4 weeks' in note and '1-2 weeks' not in note


def test_duplicate_or_missing_feed_variant_identity_is_not_silently_collapsed():
    for missing in (False, True):
        raw = json.loads(feed())
        if missing:
            raw['products'][0]['variants'][0].pop('id')
        else:
            raw['products'][0]['variants'].append(raw['products'][0]['variants'][0])
        with pytest.raises(ValueError, match='feed identities'):
            RacyclesShopifyParser().parse_listing_page(json.dumps(raw), COLLECTION)


def test_boolean_reference_is_not_an_absent_reference():
    raw = deepcopy(RAW)
    raw['variants'][0]['compare_at_price'] = False
    with pytest.raises(ValueError, match='minor-unit price'):
        detail_data(HTML, URL, raw)


def test_observed_available_preorder_map_preserves_actual_reservation_notice():
    html = (FIXTURES / 'racycles-backorder.html').read_text()
    raw = json.loads((FIXTURES / 'racycles-backorder.json').read_text())
    actual = detail_data(html, 'https://racycles.com/products/' + raw['handle'], raw)
    assert len(actual['variants']) == 5
    assert all(v['available'] and v['qty'] == 0 and not v['virtual_warehouse']
               and not v['in_stock'] for v in actual['variants'].values())
    for row in actual['variants'].values():
        assert row['shipping_note'].startswith('Coming soon! Reserve your Van Rysel')
        assert 'sales associate will contact you' in row['shipping_note']
        assert ' / XS' not in row['shipping_note']
