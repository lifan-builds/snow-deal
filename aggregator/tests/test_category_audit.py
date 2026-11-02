"""Catalog evidence regressions, including bad taxonomy and later price refreshes."""
import asyncio
import json
import sqlite3
from datetime import datetime, timezone

import pytest

from aggregator.categorizer import categorize, exclusion_reason
from aggregator.db import get_brands, get_category_counts, init_db, query_deals, upsert_deals
from aggregator.models import AggregatedDeal
from aggregator.scraper import _products_to_deals
from snow_deals.parsers.shopify import ShopifyParser, product_type_from_item


@pytest.mark.parametrize(('name', 'product_type', 'expected'), [
    ('Atomic Maverick Skis + Bindings + Boots', 'Ski Boots', 'skis'),
    ('K2 Disruption Ski + M3', 'Bindings', 'skis'),
    ('Burton Custom Snowboard + Bindings + Boots', 'Bindings', 'snowboards'),
    ('Fischer RC4 Worldcup Noize (SKI ONLY-BINDING NOT INCLUDED)', 'Skis', 'skis'),
    ('Head PR Bindings for Head PR System Skis Only', 'Skis', 'bindings'),
    ('Nordica HF 110', 'SkiBoots', 'ski boots'),
    ('Head Freeflex 14', 'Ski Bindings', 'bindings'),
    ('Vantage 2 MIPS Round Contour', 'Goggles', 'helmets'),
    ('Flight Deck M Rep Lens', 'Helmets', 'accessories'),
    ('Squad MAG + Bonus Lens', 'Snow Accessories - Goggles', 'goggles'),
    ('Model 42', 'Snow Accessories - Helmets', 'helmets'),
    ('Salomon Pearl Boa Boot', 'Boots', 'snowboard boots'),
    ('K2 Contour Boot', 'Boots', 'snowboard boots'),
    ('Scott Celeste', '', 'ski boots'),
    ('Union Reset Pro', '', 'snowboard boots'),
    ('Ride Insano', '', 'snowboard boots'),
    ('Jones Meteorite', '', 'bindings'),
    ('YES Pick Your Line', '', 'snowboards'),
    ('Kamik Hemlock Snow Boot', 'Footwear - Snow Boots - Men', 'winter boots'),
    ('Black Diamond Helio', '', 'skis'),
    ('Ski Poles', 'Ski Poles - Bindings - Binding', 'poles'),
    ('Atomic Pro Skis with Integrated Skins', 'Skis', 'skis'),
    ('Splitboard Climbing Skins', 'Snowboards', 'accessories'),
    ('Roxa Tongue Liner Ski Boot', 'Ski Boots', 'ski boots'),
    ('Replacement Boot Liner', 'Accessories', 'accessories'),
    ('Falke Troyer 1/4 Zip', 'Layers', 'layers'),
    ('Coal The Pearl', 'Beanies', 'accessories'),
    ('Atomic Mystery Model', '', None),
    ('Burton Mystery Model', '', None),
])
def test_catalog_evidence(name, product_type, expected):
    assert categorize(name, product_type=product_type) == expected


@pytest.mark.parametrize(('name', 'product_type', 'expected'), [
    ('Infants Snow Suit', '', 'children'),
    ('Atomic Redster Jrs', '', 'children'),
    ('Mystery Model', 'Ski Boots | Kids', 'children'),
    ('Patagonia Go To', 'Short Sleeve Shirt', 'non-snow'),
    ('Hyper Sprint 7', 'Running Shoes', 'non-snow'),
    ('Baggies Lights 6', 'Shorts', 'non-snow'),
    ('Seamless Leg Warmers', 'Cycling Clothing', 'non-snow'),
    ('Mens Short Cuff Ski Gloves', '', None),
    ('Vans Hi Standard Snowboard Boots', 'Snowboard Boots', None),
    ('Atlas Range Snowshoe', 'Accessories', None),
])
def test_exclusion_boundaries(name, product_type, expected):
    assert exclusion_reason(name, product_type=product_type) == expected


@pytest.mark.parametrize(('raw', 'expected'), [
    ({'product_type': 'MDED04', 'tags': ['BreadcrumbClass:Men\'s Bindings', 'BreadcrumbSubBMC:Snowboard']}, "Men's Bindings | Snowboard"),
    ({'product_type': '', 'tags': 'Gear: Ski Boots, Sale'}, 'Ski Boots'),
    ({'product_type': '', 'tags': ['Skis:']}, 'Skis'),
    ({'product_type': 'Ski Boots', 'tags': ['Kids']}, 'Ski Boots | Kids'),
])
def test_readable_taxonomy(raw, expected):
    assert product_type_from_item(raw) == expected


def test_taxonomy_survives_parser_and_filters_children():
    body = {'products': [
        {'handle': 'ultra', 'title': 'Ultra', 'vendor': 'Union', 'product_type': 'MDED04',
         'tags': ['BreadcrumbClass:Men\'s Bindings', 'BreadcrumbSubBMC:Snowboard'],
         'variants': [{'price': '100', 'compare_at_price': '200'}]},
        {'handle': 'junior', 'title': 'Ultra', 'product_type': 'Bindings', 'tags': ['Kids'],
         'variants': [{'price': '100', 'compare_at_price': '200'}]},
    ]}
    products = ShopifyParser().parse_listing_page(json.dumps(body), 'https://store.example/collections/sale/products.json')
    deals = _products_to_deals(products, 'Fixture')
    assert len(deals) == 1
    assert deals[0].category == 'bindings'
    assert deals[0].product_type == "Men's Bindings | Snowboard"


def deal(name='Mystery Model', product_type='Accessories', category='accessories'):
    return AggregatedDeal(id=None, store='Fixture', name=name, url='https://store.example/item',
                          current_price=50, original_price=100, discount_pct=50,
                          category=category, sizes=None, length_min=None, length_max=None,
                          scraped_at=datetime.now(timezone.utc).replace(tzinfo=None),
                          brand='fixture', product_type=product_type)


def test_reviewed_metadata_survives_price_refresh_but_not_changed_product(tmp_path):
    async def run():
        path = tmp_path / 'deals.db'
        await init_db(path)
        original = deal()
        await upsert_deals([original], path)
        refresh = deal(product_type='MDED04', category='skis')
        refresh.current_price = 40
        await upsert_deals([refresh], path)
        actual = (await query_deals(db_path=path))[0]
        assert (actual.product_type, actual.category, actual.current_price) == ('Accessories', 'accessories', 40)
        renamed = deal(name='New Model', product_type=None, category='snowboards')
        await upsert_deals([renamed], path)
        actual = (await query_deals(db_path=path))[0]
        assert actual.product_type is None and actual.category == 'snowboards'
        await upsert_deals([deal(name='New Model', product_type='Ski Boots', category='ski boots')], path)
        actual = (await query_deals(db_path=path))[0]
        assert actual.product_type == 'Ski Boots' and actual.category == 'ski boots'
    asyncio.run(run())


def test_reviewed_exclusion_survives_opaque_feed_and_all_public_filters(tmp_path):
    async def run():
        path = tmp_path / 'deals.db'
        await init_db(path)
        await upsert_deals([deal(product_type='Cycling Clothing', category=None)], path)
        await upsert_deals([deal(product_type='Unclassified', category='skis')], path)
        assert await query_deals(include_clothing=True, db_path=path) == []
        assert await query_deals(category='skis', db_path=path) == []
        assert await query_deals(count_only=True, db_path=path) == 0
        assert await get_category_counts(path) == {}
        assert await get_brands(path) == []
        with sqlite3.connect(path) as db:
            assert db.execute('SELECT product_type, exclusion_reason FROM deals').fetchone() == ('Cycling Clothing', 'non-snow')
    asyncio.run(run())


def test_offline_audit_requires_matching_title_and_preserves_source(tmp_path):
    from scripts.audit_categories import audit
    source = tmp_path / 'source.db'
    asyncio.run(init_db(source))
    asyncio.run(upsert_deals([deal(product_type=None, category=None)], source))
    original = source.read_bytes()
    target = tmp_path / 'audited.db'
    metadata = {'https://store.example/item': {'name': 'Different Product', 'product_type': 'Skis', 'source': 'https://store.example/feed'}}
    summary = audit(source, target, metadata, tmp_path / 'reports')
    assert summary['metadata_matches_current'] == 0
    assert summary['metadata_matches_all_rows'] == 0
    assert summary['unresolved_current'] == 1
    assert source.read_bytes() == original
    with pytest.raises(ValueError):
        audit(source, target, {}, tmp_path / 'reports')
