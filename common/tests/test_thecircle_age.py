"""Source-backed child-sizing containment preserves exact offers for exclusion."""
import json
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from aggregator.scraper import _products_to_deals
from bs4 import BeautifulSoup
from deal_common.parsers.thecircle import (
    TheCircleParser,
    _child_age_size,
    _children_sizing,
)

FIXTURES = Path(__file__).parent / 'fixtures/thecircle'
MARKER = 'Includes children sizing'


def capture(stem):
    return ((FIXTURES / (stem + '.html')).read_text(),
            json.loads((FIXTURES / (stem + '.json')).read_text()))


def parse(html, raw):
    return TheCircleParser().parse_product_evidence(html, raw['url'], json.dumps(raw))[0]


@pytest.mark.parametrize('row', json.loads((FIXTURES / 'age-manifest.json').read_text()), ids=lambda row: row['stem'])
def test_factual_age_evidence_marks_containment_without_changing_offers_and_existing_consumer_excludes(row):
    html, raw = capture(row['stem'])
    original = deepcopy(raw)
    product = parse(html, raw)
    assert product.product_type == MARKER
    expected = {key: value for key, value in raw['variants'].items()
                if value['stock']['available'] and value['price']['price_old'] > value['price']['price']}
    assert {offer.variant_key for offer in product.offers} == set(expected)
    for offer in product.offers:
        value = expected[offer.variant_key]
        assert (offer.current_price, offer.original_price, offer.url, offer.availability) == (
            value['price']['price'], value['price']['price_old'], value['url'], 'in_stock')
    before = asdict(product)
    assert _products_to_deals([product], 'The Circle Whistler') == []
    assert asdict(product) == before and raw == original


def test_mixed_child_and_adult_options_are_retained_but_existing_consumer_withholds_the_whole_family():
    html, raw = capture('jackson')
    soup = BeautifulSoup(html, 'html.parser')
    sibling = '100724075'
    raw['variants'][sibling]['title'] = '"Color: Matte Black","Size: 8-9Y"'
    raw['variants'][sibling]['stock'].update(available=True, on_stock=True, level=1)
    node = soup.select_one('.product_variants [data-vid="' + sibling + '"]')
    node['data-size'], node['data-availability'] = 'Size: 8-9Y', '1'
    option = soup.select_one('select[name="matrix[size]"] option[value="L"]')
    option['value'], option.string = '8-9Y', '8-9Y'
    product = parse(str(soup), raw)
    assert product.product_type == MARKER
    assert {offer.size for offer in product.offers} == {'8-9Y', 'XL'}
    before = [asdict(offer) for offer in product.offers]
    assert len(_products_to_deals([replace(product, product_type=None)], 'The Circle Whistler')) == 1
    assert _products_to_deals([product], 'The Circle Whistler') == []
    assert [asdict(offer) for offer in product.offers] == before
    # Full variant evidence still establishes containment when only the adult is available.
    raw['variants'][sibling]['stock'].update(available=False, on_stock=False, level=0)
    node['data-availability'] = ''
    product = parse(str(soup), raw)
    assert product.product_type == MARKER and [offer.size for offer in product.offers] == ['XL']


@pytest.mark.parametrize('stem', ['jackson', 'shapes-01', 'shapes-02', 'shapes-06', 'chino-inch', 'kader-inch'])
def test_adult_fit_numeric_inch_trouser_and_snowboard_sizes_are_not_child_evidence(stem):
    html, raw = capture(stem)
    assert parse(html, raw).product_type is None


@pytest.mark.parametrize('size', ['0-3M', '24M', '12-18m', '16Y', '10-11Y', '4T', '10T',
                                 '110/116 (5-6Y)', '74/80 (12–18 Mo)', 'L (1-2.5Y)'])
def test_only_complete_bounded_observed_age_labels_and_wrappers_establish_child_sizing(size):
    assert _child_age_size(size)


@pytest.mark.parametrize('size', [None, '18Y', '17Y', '25M', '11T', '0T', '0M', '14', 'M', 'XS',
                                 '170cm', '12-inch', '30/32', '38/40', '12"', '160W', '170 (100-110)',
                                 '110/116 (18Y)', 'XL (140-152)', '2-3', '3-2Y', '24-12M', '-2Y',
                                 '2Y extra', '2-4Y/32', '2–3–4Y'])
def test_adult_ambiguous_out_of_bound_and_bad_range_labels_are_not_repaired_or_interpreted(size):
    assert not _child_age_size(size)
    assert _children_sizing({}, [size]) is None


@pytest.mark.parametrize('fact', json.loads((FIXTURES / 'age-evidence.json').read_text()), ids=lambda row: row['name'])
def test_factual_full_variant_cohort_and_source_brand_description_evidence_is_retained(fact):
    original = deepcopy(fact)
    assert _children_sizing(fact, fact['sizes']) == fact['expected']
    assert fact == original


def miles():
    return {'brand': {'id': 2212719, 'title': 'Miles', 'url': 'https://www.thecirclewhistler.com/brands/miles/'}}


@pytest.mark.parametrize('size', ['2', '14'])
def test_exact_miles_identity_and_chart_supported_numeric_sizes_establish_only_containment(size):
    assert _children_sizing(miles(), [size]) == MARKER
    assert _children_sizing(miles(), [size, 'M', '6X']) == MARKER


@pytest.mark.parametrize('change', ['id', 'title', 'url', 'foreign_host', 'missing_brand'])
def test_manufacturer_identity_is_exact_and_never_a_global_numeric_or_brand_alias_rule(change):
    raw = miles()
    if change == 'id':
        raw['brand']['id'] = 999
    elif change == 'title':
        raw['brand']['title'] = 'Miles The Label'
    elif change == 'url':
        raw['brand']['url'] += '?other=1'
    elif change == 'foreign_host':
        raw['brand']['url'] = 'https://other.example/brands/miles/'
    else:
        raw.pop('brand')
    assert _children_sizing(raw, ['2', '14']) is None


@pytest.mark.parametrize('size', ['1', '15', '6X', 'M', 'XS', '14"', '30/32'])
def test_miles_does_not_establish_age_for_unsupported_sizes(size):
    assert _children_sizing(miles(), [size]) is None


@pytest.mark.parametrize('description', ['For a child around 140 cm.', 'Ages 10-12 years for outdoor play.',
                                      'Ages 18 years, for a child.', 'Ages 12-10 years, for a child.',
                                      'Adult size M, not a children sizing statement.'])
def test_description_requires_the_observed_explicit_bounded_child_age_clause(description):
    assert _children_sizing({'description': description}, ['M']) is None
