"""Observed manual/component offers and complete-powered-tool counterexamples."""
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.models import Product
from deal_common.offers import VariantOffer
from tool_deals.catalog import CATALOG, classify


def captured():
    return json.loads((Path(__file__).parent / 'fixtures/manual_and_accessory_offers.json').read_text())


def product(raw):
    variant = raw['variants'][0]
    price, reference = (float(Decimal(str(variant[key])) / 100) for key in ('price', 'compare_at_price'))
    return Product(raw['title'], raw['url'], price, reference, product_type=raw['product_type'],
                   brand=raw['vendor'], tags=tuple(raw['tags']), offers=[VariantOffer(
                       str(variant['id']), raw['url'] + '&variant=' + str(variant['id']), price, reference,
                       availability='in_stock')])


@pytest.mark.parametrize('raw', captured(), ids=lambda r: r['product_type'] + '-' + str(r['variants'][0]['id']))
def test_observed_manual_tools_bits_and_sanding_pads_are_excluded_without_mutation(raw):
    item = product(raw)
    original = deepcopy(item)
    assert classify(item) is None
    assert normalize([item], CATALOG, urlsplit(item.url).hostname) == []
    assert item == original


@pytest.mark.parametrize(('title', 'kind'), [
    ('Impact Nutsetter for Cordless Impact Driver', 'Power Tools'),
    ('Power Nut Setter Compatible with Electric Drill', 'Drills'),
    ('Lobular Power Nut Driver 1-7/8 in.', 'Nut Driver'),
    ('Nut Driver for Cordless Drill', 'Nut Driver'),
    ('FrameMaster Point Driver for Electric Drill', 'Point Driver'),
    ('Point Driver Compatible with Pneumatic Tools', 'Point Driver'),
    ('Cordless Drill Compatible Point Driver', 'Point Driver'),
    ('Cordless Drill Compatible Power Nut Driver', 'Nut Driver'),
    ('Electric Drill Compatible Hacksaw', 'Hacksaw'),
    ('Hand Hacksaw for Cordless Saw', 'Hacksaw'),
    ('Hacksaw Including Electric Drill', 'Hacksaw'),
    ('Oscillating Tool Sanding Pad Compatible with Cordless Sander', 'Power Tools'),
    ('Sanding Pads for 18V Oscillating Tool', 'Power Tools'),
    ('Sanding Pad with Free Cordless Sander', 'Power Tools'),
    ('Cordless Oscillating Tool', 'Oscillating Tool Access'),
    ('Non-powered Hacksaw', 'Hacksaw'),
    ('Hand-Powered Point Driver', 'Point Driver'),
    ('Hand-Operated Cordless Point Driver', 'Point Driver'),
    ('Manual Pneumatic Nut Driver', 'Nut Driver'),
])
def test_component_and_compatibility_identity_never_borrows_powered_keywords(title, kind):
    assert classify(Product(title, 'https://example.com/products/tool', 100, 200, product_type=kind)) is None


@pytest.mark.parametrize(('title', 'kind', 'form'), [
    ('Electric Point Driver', 'Point Driver', 'Not specified'),
    ('Cordless Point Driver Kit', 'Point Driver', 'Kit'),
    ('Pneumatic Point Driver with Points', 'Point Driver', 'Not specified'),
    ('Pneumatic Point Driver Compatible with Mounting Hardware', 'Point Driver', 'Not specified'),
    ('Battery-Powered Point Driver', 'Point Driver', 'Not specified'),
    ('Corded Hacksaw', 'Hacksaw', 'Not specified'),
    ('Electric Hack Saw', 'Hacksaw', 'Not specified'),
    ('Cordless Hacksaw with Blade Kit', 'Hacksaw', 'Not specified'),
    ('Pneumatic Nut Driver', 'Nut Driver', 'Not specified'),
    ('Cordless Impact Driver Kit with Nutsetter Bits', 'Power Tools', 'Kit'),
    ('Orbital Sander Kit with Sanding Pads', 'Sanders', 'Kit'),
    ('Cordless Oscillating Tool Kit Including Sanding Pad', 'Power Tools', 'Kit'),
    ('Pneumatic Point Driver Kit w/ Nut Driver Bits', 'Point Driver', 'Kit'),
    ('Electric Point Driver with Owner Manual', 'Point Driver', 'Not specified'),
    ('Cordless Point Driver Including Manual', 'Point Driver', 'Not specified'),
    ('Pneumatic Point Driver Compatible with Hand-Operated Hardware', 'Point Driver', 'Not specified'),
    ('Handheld Cordless Point Driver', 'Point Driver', 'Not specified'),
    ('Non-Electric Pneumatic Nut Driver', 'Nut Driver', 'Not specified'),
])
def test_explicit_powered_machines_and_complete_kits_with_included_accessories_survive(title, kind, form):
    actual = classify(Product(title, 'https://example.com/products/tool', 100, 200, product_type=kind))
    assert actual is not None
    assert (actual.category, actual.format, actual.platform) == ('Power tools', form, '')


def test_exclusions_do_not_change_surviving_exact_offers_or_default_population():
    bad = [product(raw) for raw in captured()]
    good_url = 'https://www.maxwarehouse.com/products/orbital-sander'
    exact = VariantOffer('powered-kit', good_url + '?variant=powered-kit', 120, 240, size='M',
                         options='Complete kit', availability='in_stock', availability_note='')
    good = Product('Orbital Sander Kit with Sanding Pads', good_url, 120, 240,
                   product_type='Sanders', brand='Maker', offers=[exact])
    before = deepcopy([*bad, good])
    normalized = normalize([*bad, good], CATALOG, 'www.maxwarehouse.com')
    assert len(normalized) == 1 and normalized[0]['offers'][0] == asdict(exact)
    sources = [{'name': 'Max Warehouse', 'successful_at': datetime.now(UTC).isoformat(), 'products': normalized}]
    filters = {'min_reference': 0, 'min_discount': 0, 'max_price': 0, 'stock': True, 'page': 1}
    all_prices = query(sources, filters)
    default = query(sources, {**filters, 'min_reference': CATALOG.default_reference})
    assert all_prices['total'] == default['total'] == 1
    assert all_prices['cards'][0]['offer']['variant_key'] == 'powered-kit'
    assert all_prices['cards'][0]['offer']['url'] == exact.url
    assert all_prices['cards'][0]['offer']['size'] == 'M'
    assert [*bad, good] == before
