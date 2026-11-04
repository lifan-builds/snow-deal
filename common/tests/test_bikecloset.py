import asyncio
import json
from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from cycling_deals.catalog import CATALOG
from deal_common.catalog.audit import audit_sample, validate_bikecloset_product
from deal_common.catalog.query import query
from deal_common.catalog.refresh import refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.parsers.bikecloset import (
    API,
    BikeClosetParser,
    decode_offer,
    listing_url,
    notices,
    offer_destination,
    validate_detail,
)

URL = 'https://bikecloset.com/product/test-frameset/'


def parent():
    return {'id': 12, 'type': 'variable', 'parent': 0, 'name': 'Test Frameset', 'sku': '',
            'permalink': URL, 'short_description': '<p>Brand New With Warranty!</p><p>Frames are final sale.</p>',
            'description': 'Product photos show a complete bike for reference.',
            'categories': [{'name': 'LOOK'}],
            'attributes': [{'name': 'Color', 'taxonomy': 'pa_color', 'has_variations': True,
                            'terms': [{'name': 'Black', 'slug': 'black'}, {'name': 'Rose', 'slug': 'rose'}]},
                           {'name': 'Size', 'taxonomy': 'pa_size', 'has_variations': True,
                            'terms': [{'name': 'Small', 'slug': 'small'}, {'name': 'Large', 'slug': 'large'}]}],
            'variations': [{'id': 13, 'attributes': [{'name': 'Color', 'value': 'black'}, {'name': 'Size', 'value': 'small'}]},
                           {'id': 14, 'attributes': [{'name': 'Color', 'value': 'rose'}, {'name': 'Size', 'value': 'large'}]}]}


def variation(large=False):
    return {'id': 14 if large else 13, 'parent': 12, 'type': 'variation', 'name': 'Test Frameset',
            'permalink': URL + ('?attribute_pa_size=large&attribute_pa_color=rose' if large else
                                '?attribute_pa_color=black&attribute_pa_size=small'),
            'sku': 'sku-large' if large else 'sku-small',
            'is_in_stock': True, 'is_purchasable': True, 'is_on_backorder': False,
            'prices': {'currency_code': 'USD', 'currency_minor_unit': 2, 'price': '79900', 'regular_price': '200000'},
            'images': [{'src': 'https://bikecloset.com/frame.jpg', 'thumbnail': 'https://bikecloset.com/frame-small.jpg',
                        'srcset': 'https://bikecloset.com/frame-small.jpg 200w, https://bikecloset.com/frame-medium.jpg 720w'}]}


def detail(p):
    schema = {'@type': 'Product', 'url': p['permalink'], 'name': p['name'], 'sku': p['sku'] or p['id'],
              'description': p['short_description'], 'offers': [{'priceCurrency': 'USD'}]}
    return (f'<link rel="canonical" href="{p["permalink"]}">'
            f'<form class="variations_form" action="{p["permalink"]}" data-product_id="{p["id"]}"></form>'
            f'<script type="application/ld+json">{json.dumps({"@graph": [schema]})}</script>')


def test_exact_variant_currency_price_image_and_safe_destination():
    offer = decode_offer(parent(), variation())
    assert (offer.size, offer.current_price, offer.original_price, offer.availability) == ('Small', 799, 2000, 'in_stock')
    assert offer.options == 'Color: Black / Size: Small / SKU sku-small'
    assert offer.image_url == 'https://bikecloset.com/frame-medium.jpg'
    assert 'Frameset only' in offer.availability_note and 'Final sale' in offer.availability_note
    assert offer_destination(offer.url, offer.variant_key)
    for bad in (offer.url + '&add-to-cart=12', offer.url + '&attribute_pa_size=large', offer.url.replace('small', 'large')):
        assert not offer_destination(bad, offer.variant_key)


@pytest.mark.parametrize('case', ['parent', 'currency', 'minor-unit', 'nonfinite', 'unknown-stock', 'options', 'destination'])
def test_conflicting_variant_evidence_is_rejected(case):
    p, v = parent(), variation()
    if case == 'parent': v['parent'] = 99
    elif case == 'currency': v['prices']['currency_code'] = 'CAD'
    elif case == 'minor-unit': v['prices']['currency_minor_unit'] = True
    elif case == 'nonfinite': v['prices']['price'] = 'NaN'
    elif case == 'unknown-stock': v['is_in_stock'] = None
    elif case == 'options': p['variations'][0]['attributes'].pop()
    else: v['permalink'] = v['permalink'].replace('test-frameset', 'another-frame')
    with pytest.raises(ValueError): decode_offer(p, v)


def test_backorders_used_missing_condition_and_full_price_are_excluded():
    for change in ({'is_on_backorder': True}, {'is_in_stock': False}, {'is_purchasable': False}):
        assert decode_offer(parent(), {**variation(), **change}) is None
    for description in ('', 'Used frame, formerly brand new.', 'Open box, brand new.'):
        p = parent(); p['short_description'] = description
        assert decode_offer(p, variation()) is None
    v = variation(); v['prices']['price'] = '200000'
    assert decode_offer(parent(), v) is None


def test_title_size_conflict_cannot_become_stock_or_exact_fit():
    p, v = parent(), variation()
    p['name'] = v['name'] = 'Test Frameset SIZE L (Max 25mm)'
    assert decode_offer(p, v) is None
    p['name'] = v['name'] = 'Test Frameset SIZE S (Max 25mm)'
    assert decode_offer(p, v).size == 'Small'


def test_shipping_scope_and_restrictions_override_stock_without_inventing_arrival():
    p = parent()
    p['short_description'] += '<p>Size large Rose will ship to you mid September.</p><p>Cannot ship to Hawaii Or Alaska.</p>'
    assert decode_offer(p, variation()).availability == 'in_stock'
    delayed = decode_offer(p, variation(True))
    assert delayed.availability == 'unknown'
    assert 'mid September' in delayed.availability_note and 'Cannot ship to Hawaii Or Alaska.' in delayed.availability_note
    assert notices(p, {'Size': 'Large'})[0]  # missing color metadata cannot narrow the notice
    p['short_description'] += '<p>Will ship to you late November.</p>'
    assert decode_offer(p, variation()).availability == 'unknown'


def test_detail_binding_accepts_typographic_punctuation_but_rejects_changed_notice():
    p = parent(); p['name'] = 'Test D&#8217;Huez Frameset'
    html = detail(p).replace('D&#8217;Huez', "D'Huez")
    validate_detail(html, p)
    with pytest.raises(ValueError): validate_detail(html.replace('data-product_id="12"', 'data-product_id="99"'), p)
    with pytest.raises(ValueError): validate_detail(html.replace('Frames are final sale.', 'Will ship next month.'), p)


def test_shipping_color_qualifier_requires_a_unique_explicit_attribute_term():
    p = parent()
    p['short_description'] += 'Size large Rose will ship to you mid September.'
    p['attributes'][0]['terms'][1]['name'] = 'V46 Rose'
    assert decode_offer(p, variation(True)).availability == 'unknown'
    assert decode_offer(p, variation()).availability == 'in_stock'
    p['attributes'][0]['terms'][0]['name'] = 'V99 Rose'
    assert decode_offer(p, variation()).availability == 'unknown'
    p['short_description'] = p['short_description'].replace('Rose will', 'UnknownColor will')
    assert decode_offer(p, variation()).availability == 'unknown'


def test_pagination_uses_response_totals_and_rejects_truncation_duplicates_and_drift():
    p = BikeClosetParser()
    rows = [{**parent(), 'id': i + 1} for i in range(100)]
    p.validate_listing_response(json.dumps(rows), listing_url(), {'x-wp-total': '101', 'x-wp-totalpages': '2'})
    assert p.get_next_page_url('', listing_url()) == listing_url(2)
    with pytest.raises(ValueError):
        p.validate_listing_response(json.dumps([parent()]), listing_url(2), {'x-wp-total': '101', 'x-wp-totalpages': '2'})
    p.validate_listing_response(json.dumps([{**parent(), 'id': 101}]), listing_url(2), {'x-wp-total': '101', 'x-wp-totalpages': '2'})
    assert p.get_next_page_url('', listing_url(2)) is None
    with pytest.raises(ValueError): BikeClosetParser().get_next_page_url('', listing_url())
    for rows, total in (([parent(), parent()], '2'), ([parent()], '2')):
        with pytest.raises(ValueError):
            BikeClosetParser().validate_listing_response(json.dumps(rows), listing_url(),
                                                        {'x-wp-total': total, 'x-wp-totalpages': '1'})


def test_full_refresh_audit_exact_size_and_failed_refresh_preservation(tmp_path):
    source = RetailerConfig('Bike Closet', 'bikecloset.com', [listing_url()], parser_type='bikecloset')
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'cycling.db'
    p = parent(); p['short_description'] += '<p>Size large Rose will ship to you mid September.</p>'
    broken = False
    requested = []

    def handler(request):
        requested.append(str(request.url))
        assert request.method == 'GET' and 'add-to-cart' not in str(request.url)
        if request.url.path == '/product/test-frameset/': return httpx.Response(200, text=detail(p))
        if request.url.path.endswith('/12'): return httpx.Response(200, json=p)
        if request.url.path.endswith('/13'): return httpx.Response(200, json=variation())
        if request.url.params.get('type') == 'variation':
            return httpx.Response(200, json=[variation()] if broken else [variation(), variation(True)])
        return httpx.Response(200, json=[p], headers={'x-wp-total': '1', 'x-wp-totalpages': '1'})

    transport = httpx.MockTransport(handler)
    assert asyncio.run(refresh(catalog, path, delay=0, transport=transport))[0]['status'] == 'complete'
    sources = read_sources(path, 'cycling')
    baseline = deepcopy(sources[0])
    product = sources[0]['products'][0]
    offer = next(o for o in product['offers'] if o['availability'] == 'in_stock')
    card = {**product, 'store': source.name, 'offer': offer}
    audit = asyncio.run(audit_sample([card], {source.name: source.domain}, delay=0, transport=transport))
    assert audit[0]['status'] == 'match' and audit[0]['evidence_url'] == API + '/13'
    fresh = variation(); fresh['prices']['price'] = '89900'
    assert validate_bikecloset_product(card, p, fresh)['checks']['price'] is False
    filters = {'min_reference': 1000, 'max_price': 0, 'min_discount': 0, 'stock': True, 'page': 1, 'size': 'large'}
    assert query(sources, filters)['total'] == 0
    broken = True
    assert asyncio.run(refresh(catalog, path, delay=0, transport=transport))[0]['status'] == 'incomplete'
    after = read_sources(path, 'cycling')[0]
    assert (after['products'], after['successful_at']) == (baseline['products'], baseline['successful_at'])
