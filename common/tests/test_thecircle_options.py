"""Observed CSV inch labels and narrowly proved native/hidden-DOM agreement."""
import csv
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from deal_common.parsers.thecircle import (
    ORIGIN,
    TheCircleParser,
    _html_data,
    _options,
    detail_data,
)

FIXTURES = Path(__file__).parent / 'fixtures/thecircle'
URL = ORIGIN + '/authentic-chino-loose-pant-68489662.html'
SELECTED = '115322192'


def capture(stem='chino-inch'):
    # Reduced factual pairs from profile/responses/0226+0227 and 0352+0353.
    return ((FIXTURES / (stem + '.html')).read_text(),
            json.loads((FIXTURES / (stem + '.json')).read_text()))


def csv_options(options):
    output = io.StringIO()
    csv.writer(output, quoting=csv.QUOTE_ALL).writerow([f'{key.title()}: {value}' for key, value in options.items()])
    return output.getvalue().strip()


@pytest.mark.parametrize(('label', 'expected'), [
    ('Size : 160W', {'size': '160W'}),
    ('Color : Shmobb Collab.', {'color': 'Shmobb Collab.'}),
    ('"Color: Matte Black","Size: XL"', {'color': 'Matte Black', 'size': 'XL'}),
    ('"Color: Matte Black",Size: XL', {'color': 'Matte Black', 'size': 'XL'}),
    ('  "Color: Matte Black", "Size: XL"  ', {'color': 'Matte Black', 'size': 'XL'}),
    ('"Color: Dried Kelp Green","Size: 22"""', {'color': 'Dried Kelp Green', 'size': '22"'}),
    ('"Color: Red, White","Size: 22"""', {'color': 'Red, White', 'size': '22"'}),
    ('"Color: The ""Blue"" Hour","Size: 30"""', {'color': 'The "Blue" Hour', 'size': '30"'}),
    ('"Color: Blue: Grey","Size: 30"""', {'color': 'Blue: Grey', 'size': '30"'}),
])
def test_option_labels_preserve_unquoted_single_and_csv_commas_and_doubled_quotes(label, expected):
    assert _options(label) == expected


@pytest.mark.parametrize('label', [
    None, '', ' ', '"Size: 22', '"Size: 22"junk', '"Size: 22""',
    '"Color: Blue",,"Size: M"', '"Size: M",', '""',
    '"Size"', '": M"', '"Size: "', '"Size: M","size: L"',
    '"Color: Blue"\n"Size: M"',
    '"Color: Blue",Size: 22"', '"Color: Blue",Size: 22""',
    '"Color: Blue",Si"ze: XL', '"Color: Blue",Size: M"trash',
])
def test_malformed_or_ambiguous_options_fail_instead_of_repairing_or_merging(label):
    with pytest.raises(ValueError):
        _options(label)


@pytest.mark.parametrize(('stem', 'sizes', 'available'), [
    ('chino-inch', list(range(22, 31)), 8), ('kader-inch', [26, 32, 34], 2),
])
def test_factual_csv_and_unique_native_values_reconcile_only_numeric_hidden_inch_omission(stem, sizes, available):
    html, raw = capture(stem)
    url = raw['url']
    original = deepcopy(raw)
    actual = _html_data(html, url)
    native_sizes = [o['value'] for o in BeautifulSoup(html, 'html.parser').select('select[name="matrix[size]"] option')]
    decoded = {key: _options(value['title']) for key, value in raw['variants'].items()}
    assert native_sizes == [str(size) + '"' for size in sizes]
    assert [value['size'] for value in decoded.values()] == native_sizes
    assert _options(raw['variant']) == actual['selection'] == decoded[str(raw['vid'])]
    assert [row['options']['size'] for row in actual['variants'].values()] == [str(size) for size in sizes]
    product = TheCircleParser().parse_product_evidence(html, url, json.dumps(raw))[0]
    expected = {key: row for key, row in raw['variants'].items() if row['stock']['available']}
    assert len(expected) == available
    assert {offer.variant_key for offer in product.offers} == set(expected)
    for offer in product.offers:
        row = expected[offer.variant_key]
        assert offer.size == decoded[offer.variant_key]['size']
        assert (offer.current_price, offer.original_price, offer.url, offer.availability) == (
            row['price']['price'], row['price']['price_old'], row['url'], 'in_stock')
    assert raw == original


def consistent_synthetic_dom():
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    for size, node in zip(range(22, 31), soup.select('.product_variants [data-vid]'), strict=True):
        node['data-size'] = f'Size: {size}"'
    return soup, raw


def test_synthetic_agreeing_dom_keeps_exact_inch_sizes_prices_stock_and_destinations():
    soup, raw = consistent_synthetic_dom()
    original = deepcopy(raw)
    product = TheCircleParser().parse_product_evidence(str(soup), URL, json.dumps(raw))[0]
    expected = {key: row for key, row in raw['variants'].items() if row['stock']['available']}
    assert len(expected) == 8
    assert {offer.variant_key for offer in product.offers} == set(expected)
    for offer in product.offers:
        row = expected[offer.variant_key]
        assert offer.size == _options(row['title'])['size']
        assert offer.size.endswith('"') and offer.availability == 'in_stock'
        assert (offer.current_price, offer.original_price, offer.url) == (
            row['price']['price'], row['price']['price_old'], row['url'])
        assert offer.options == 'Color: Dried Kelp Green / Size: ' + offer.size
    assert raw == original


@pytest.mark.parametrize('change', ['hidden_size', 'selected_size', 'top_variant', 'unavailable_csv'])
def test_csv_decoding_keeps_exact_dom_selected_and_unavailable_variant_guards(change):
    soup, raw = consistent_synthetic_dom()
    if change == 'hidden_size':
        soup.select_one('.product_variants [data-vid="' + SELECTED + '"]')['data-size'] = 'Size: 21'
    elif change == 'selected_size':
        soup.select_one('select[name="matrix[size]"] option[selected]')['value'] = '22'
    elif change == 'top_variant':
        raw['variant'] = '"Color: Dried Kelp Green","Size: 23"""'
    else:
        unavailable = next(row for row in raw['variants'].values() if not row['stock']['available'])
        unavailable['title'] = '"Color: Dried Kelp Green","Size: 27""'
    with pytest.raises(ValueError):
        detail_data(str(soup), URL, json.dumps(raw))


@pytest.mark.parametrize('variant_id', [SELECTED, '115322194', '115322197'])
def test_unescaped_csv_quote_fails_full_binding_even_for_unavailable_sibling(variant_id):
    html, raw = capture()
    options = _options(raw['variants'][variant_id]['title'])
    malformed = '"Color: Dried Kelp Green",Size: ' + options['size']
    raw['variants'][variant_id]['title'] = malformed
    if variant_id == SELECTED:
        raw['variant'] = malformed
    with pytest.raises(ValueError, match='malformed variant options'):
        detail_data(html, URL, json.dumps(raw))


@pytest.mark.parametrize('change', ['duplicate_native', 'unquoted_alternative', 'missing_native',
                                  'wrong_number', 'wrong_color', 'color_quote', 'requested_id'])
def test_numeric_inch_exception_requires_exact_unique_native_choice_and_other_literal_facts(change):
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    selected = soup.select_one('select[name="matrix[size]"] option[selected]')
    node = soup.select_one('.product_variants [data-vid="' + SELECTED + '"]')
    url = URL
    if change in {'duplicate_native', 'unquoted_alternative'}:
        other = deepcopy(selected)
        other.attrs.pop('selected')
        if change == 'unquoted_alternative':
            other['value'] = '22'
        selected.parent.append(other)
    elif change == 'missing_native':
        selected['value'] = '22'
    elif change == 'wrong_number':
        node['data-size'] = 'Size: 23'
    elif change == 'wrong_color':
        node['data-color'] = 'Color: Other Green'
    elif change == 'color_quote':
        options = _options(raw['variants'][SELECTED]['title'])
        options['color'] += '"'
        raw['variants'][SELECTED]['title'] = raw['variant'] = csv_options(options)
        soup.select_one('select[name="matrix[color]"] option[selected]')['value'] = options['color']
    else:
        url += '?id=115322194'
    with pytest.raises(ValueError):
        detail_data(str(soup), url, json.dumps(raw))


@pytest.mark.parametrize('quoted', [False, True])
def test_full_option_tuple_collision_across_ids_fails_even_without_native_unquoted_alternative(quoted):
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    sibling = '115322194'
    options = _options(raw['variants'][sibling]['title'])
    options['size'] = '22"' if quoted else '22'
    raw['variants'][sibling]['title'] = csv_options(options)
    soup.select_one('.product_variants [data-vid="' + sibling + '"]')['data-size'] = 'Size: 22'
    with pytest.raises(ValueError, match='ambiguous inch-size variants'):
        detail_data(str(soup), URL, json.dumps(raw))


@pytest.mark.parametrize(('api_size', 'dom_size'), [
    ('M"', 'M'), ('22.5"', '22.5'), ('22""', '22"'), ('"22"', '"22'),
    ('22" wide', '22 wide'), ('22\u2033', '22'), ('22', '22"'),
])
def test_other_size_quotes_units_and_non_numeric_values_are_not_normalized(api_size, dom_size):
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    options = _options(raw['variants'][SELECTED]['title'])
    options['size'] = api_size
    raw['variants'][SELECTED]['title'] = raw['variant'] = csv_options(options)
    soup.select_one('select[name="matrix[size]"] option[selected]')['value'] = api_size
    soup.select_one('.product_variants [data-vid="' + SELECTED + '"]')['data-size'] = 'Size: ' + dom_size
    with pytest.raises(ValueError):
        detail_data(str(soup), URL, json.dumps(raw))
