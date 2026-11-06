"""Captured selected-sold-out and exact singleton Default purchase panels."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from deal_common.parsers.thecircle import TheCircleParser, detail_data

FIXTURES = Path(__file__).parent / 'fixtures/thecircle'
MANIFEST = json.loads((FIXTURES / 'structural-manifest.json').read_text())


def capture(stem):
    return ((FIXTURES / (stem + '.html')).read_text(),
            json.loads((FIXTURES / (stem + '.json')).read_text()))


def parse(html, raw, url=None):
    return TheCircleParser().parse_product_evidence(html, url or raw['url'], json.dumps(raw))


@pytest.mark.parametrize('row', MANIFEST, ids=lambda row: row['stem'])
def test_retained_structural_and_exact_selected_pairs_preserve_every_available_variant_fact(row):
    html, raw = capture(row['stem'])
    original = deepcopy(raw)
    parser = TheCircleParser()
    parser.product_ids[raw['url']] = row['product_id']
    assert parser.get_product_evidence_url(html, row['url']) == row['url'].replace('.html', '.ajax')
    actual = detail_data(html, row['url'], json.dumps(raw))
    assert actual['id'] == row['product_id'] and actual['selected'] == row['selected']
    assert len(actual['variants']) == row['variant_count']
    products = parser.parse_product_evidence(html, row['url'], json.dumps(raw))
    expected = {key: value for key, value in raw['variants'].items()
                if value['stock']['available'] and value['price']['price_old'] > value['price']['price']}
    assert len(products) == bool(expected)
    offers = {offer.variant_key: offer for offer in products[0].offers} if products else {}
    assert set(offers) == set(expected)
    for key, offer in offers.items():
        value = expected[key]
        assert (offer.current_price, offer.original_price, offer.url, offer.availability) == (
            value['price']['price'], value['price']['price_old'], value['url'], 'in_stock')
        assert offer.options == ' / '.join(f'{k.title()}: {v}' for k, v in actual['variants'][key]['options'].items())
        assert offer.size == actual['variants'][key]['size']
    if row['stem'].startswith('soldout-'):
        assert actual['variants'][row['selected']]['availability'] == 'out_of_stock'
        assert row['selected'] not in offers and offers  # Available siblings survive.
    if row['stem'] == 'default-bag':
        assert offers[row['selected']].size is None and offers[row['selected']].options == ''
    assert raw == original


@pytest.mark.parametrize('stem', ['jackson', 'soldout-shirt'])
@pytest.mark.parametrize('change', ['missing', 'duplicate', 'wrong_pid', 'malformed', 'wrong_name', 'outside_form'])
def test_quantity_identity_is_required_once_in_the_main_form_for_both_button_shapes(stem, change):
    html, raw = capture(stem)
    soup = BeautifulSoup(html, 'html.parser')
    node = soup.select_one('#product_configure_form input[name="quantity"]')
    if change == 'missing':
        node.decompose()
    elif change == 'duplicate':
        node.parent.append(deepcopy(node))
    elif change == 'wrong_pid':
        node['id'] = 'qty_999'
    elif change == 'malformed':
        node['id'] += '_extra'
    elif change == 'wrong_name':
        node['name'] = 'related_quantity'
    else:
        soup.body.append(node.extract())
    with pytest.raises(ValueError):
        parse(str(soup), raw)


@pytest.mark.parametrize('change', ['pid', 'vid', 'partial'])
def test_present_purchase_button_must_agree_with_quantity_product_and_selected_form(change):
    html, raw = capture('jackson')
    soup = BeautifulSoup(html, 'html.parser')
    button = soup.select_one('#product_configure_form [data-pid][data-vid]')
    if change == 'partial':
        button.attrs.pop('data-vid')
    else:
        button['data-' + change] = '999'
    with pytest.raises(ValueError):
        parse(str(soup), raw)


@pytest.mark.parametrize('change', ['missing_control', 'control_text', 'control_class', 'active_panel',
                                  'partial_button', 'unknown', 'untracked', 'missing_level', 'backorders'])
def test_absent_purchase_identity_requires_explicit_soldout_control_and_independent_zero_stock(change):
    html, raw = capture('soldout-shirt')
    soup = BeautifulSoup(html, 'html.parser')
    button = soup.select_one('#product_configure_form button.out')
    if change == 'missing_control':
        button.decompose()
    elif change == 'control_text':
        button.string = 'Check availability'
    elif change == 'control_class':
        button['class'] = ['btn']
    elif change == 'active_panel':
        soup.select_one('meta[itemprop="availability"]')['content'] = 'https://schema.org/InStock'
    elif change == 'partial_button':
        button['data-pid'] = str(raw['id'])
    else:
        updates = {'unknown': {'available': None}, 'untracked': {'track': False},
                   'missing_level': {'level': None}, 'backorders': {'allow_backorders': True}}[change]
        raw['variants'][str(raw['vid'])]['stock'].update(updates)
        raw['stock'].update({('allow_outofstock_sale' if key == 'allow_backorders' else key): value
                             for key, value in updates.items()})
    with pytest.raises(ValueError):
        parse(str(soup), raw)


def test_soldout_quantity_identity_does_not_replace_discovery_or_requested_variant_checks():
    html, raw = capture('soldout-shirt')
    parser = TheCircleParser()
    parser.product_ids[raw['url']] = '999'
    with pytest.raises(ValueError, match='discovery/detail'):
        parser.parse_product_evidence(html, raw['url'], json.dumps(raw))
    with pytest.raises(ValueError, match='substituted'):
        parse(html, raw, raw['url'] + '?id=96386692')


@pytest.mark.parametrize('change', ['extra_api', 'extra_dom', 'extra_native', 'wrong_native_id',
                                  'unselected', 'native_label', 'native_price', 'matrix_control',
                                  'other_control', 'title', 'false_default', 'missing_default',
                                  'integer_default', 'top_variant', 'dom_color', 'dom_size'])
def test_default_requires_coherent_one_id_native_dom_endpoint_and_price_evidence(change):
    html, raw = capture('default-bag')
    soup = BeautifulSoup(html, 'html.parser')
    selected = str(raw['vid'])
    native = soup.select_one('select[name="variant"]')
    option = native.select_one('option')
    node = soup.select_one('.product_variants [data-vid]')
    if change == 'extra_api':
        raw['variants']['999'] = {**raw['variants'][selected], 'id': 999, 'url': raw['url'] + '?id=999'}
    elif change == 'extra_dom':
        other = deepcopy(node)
        other['data-vid'] = '999'
        node.parent.append(other)
    elif change == 'extra_native':
        other = deepcopy(option)
        other['value'] = '999'
        other.attrs.pop('selected')
        native.append(other)
    elif change == 'wrong_native_id':
        option['value'] = '999'
    elif change == 'unselected':
        option.attrs.pop('selected')
    elif change == 'native_label':
        option.string = 'One Size - C$40.00'
    elif change == 'native_price':
        option.string = 'Default - C$41.00'
    elif change in {'matrix_control', 'other_control'}:
        other = deepcopy(native)
        other['name'] = 'matrix[size]' if change == 'matrix_control' else 'dimension'
        native.parent.append(other)
    elif change == 'title':
        raw['variants'][selected]['title'] = 'One Size'
    elif change == 'false_default':
        raw['variants'][selected]['default'] = False
    elif change == 'missing_default':
        raw['variants'][selected].pop('default')
    elif change == 'integer_default':
        raw['variants'][selected]['default'] = 1
    elif change == 'top_variant':
        raw['variant'] = 'Default'
    elif change == 'dom_color':
        node['data-color'] = 'Color: Default'
    else:
        node['data-size'] = 'One Size'
    with pytest.raises(ValueError):
        parse(str(soup), raw)


def test_default_never_promotes_incomplete_stock_to_in_stock_or_fabricates_size():
    html, raw = capture('default-bag')
    raw['variants'][str(raw['vid'])]['stock']['track'] = raw['stock']['track'] = False
    offer = parse(html, raw)[0].offers[0]
    assert offer.availability == 'unknown' and offer.availability_note
    assert offer.size is None and offer.options == ''


@pytest.mark.parametrize('stem', ['chino-inch-23', 'default-bag'])
@pytest.mark.parametrize('change', ['disabled', 'aria_disabled', 'out_class', 'out_text', 'not_button',
                                  'duplicate', 'other_button', 'decoy_out_control'])
def test_present_purchase_identity_cannot_override_contradictory_or_ambiguous_primary_control(stem, change):
    html, raw = capture(stem)
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.select_one('#product_configure_form')
    button = form.select_one('button[data-pid][data-vid]')
    if change == 'disabled':
        button['disabled'] = 'disabled'
    elif change == 'aria_disabled':
        button['aria-disabled'] = 'true'
    elif change == 'out_class':
        button['class'].append('out')
    elif change == 'out_text':
        button.string = 'Out of Stock'
    elif change == 'not_button':
        button.name = 'div'
    elif change == 'duplicate':
        form.append(deepcopy(button))
    else:
        other = soup.new_tag('button', attrs={'type': 'button'})
        other.string = 'Other control'
        if change == 'decoy_out_control':
            other['class'] = ['out']
            other['hidden'] = ''
            other.string = 'Out of Stock'
        form.append(other)
    with pytest.raises(ValueError):
        parse(str(soup), raw)
