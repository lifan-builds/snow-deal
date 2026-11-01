"""Regression fixtures from the November source-quality audit."""
import asyncio
import json
from pathlib import Path

import httpx
import pytest

from aggregator.browser import _parse_raw_products
from aggregator.categorizer import categorize, is_excluded
from aggregator.config import StoreConfig
from aggregator.parsers.coloradodiscount import ColoradoDiscountParser
from aggregator.parsers.sacredride import SacredRideParser
from aggregator.scraper import _products_to_deals, build_scrape_report, protect_partial_snapshots, scrape_store
from snow_deals.models import Product
from snow_deals.parsers.bluezone import BlueZoneParser
from snow_deals.parsers.shopify import ShopifyParser


@pytest.mark.parametrize(('name', 'expected'), [
    ('Oakley Kendall RC Shell Snow Pant', 'pants'),
    ('Helly Hansen Sogn Bib Shell Pant', 'pants'),
    ('Jet Set Magic Ghoster Ski Suit', 'jackets'),
    ('Atomic Redster G7 Skis w/M12 GW Bindings NEW 168cm', 'skis'),
    ('Unleashed 108', 'skis'),
    ('CAPiTA Mercury Snowboard', 'snowboards'),
    ('Vans Hi Standard Snowboard Boots', 'snowboard boots'),
])
def test_real_product_categories(name, expected):
    assert not is_excluded(name)
    assert categorize(name) == expected


def test_collection_path_cannot_override_product_name():
    assert categorize('Oakley Shell Snow Pant', '/collections/skis/products/shell-pant') == 'pants'
    assert categorize('Model 100', '/collections/skis/products/model', 'Ski Boots') == 'ski boots'
    assert is_excluded('Trucker Cap')
    assert is_excluded('Vans Classic Skate Shoe')


def test_static_images_and_explicit_lengths():
    colorado = '''<li class="prod"><a name="8618"></a>
    <a title="2025 Redster G7 Skis" href="/store/redster.html"><img src="/images/redster.jpg"></a>
    <a class="bb-prodnme" href="/store/redster.html">Atomic Redster G7 Skis w/M12 GW Bindings NEW 168cm</a>
    <span>$850.00$349.99</span></li>'''
    p = ColoradoDiscountParser().parse_listing_page(colorado, 'https://store.test/list')[0]
    assert p.image_url == 'https://store.test/images/redster.jpg'
    assert p.sizes == ['168cm']
    assert p.current_price == 349.99
    assert p.original_price == 850
    deal = _products_to_deals([p], 'Test')[0]
    assert deal.category == 'skis' and deal.length_min == 168
    for parser, html in [
        (BlueZoneParser(), '<div class="card product-card"><h3><a href="/ski">Atomic Skis</a></h3><div class="product-price"><del>$600</del><span class="text-accent">$300</span></div><img src="/img.jpg"></div>'),
        (SacredRideParser(), '<li class="product"><a href="/product/ski"><h2>Atomic Skis</h2></a><del><span class="woocommerce-Price-amount">$600</span></del><ins><span class="woocommerce-Price-amount">$300</span></ins><img data-src="/img.jpg" src="data:image/gif;base64,placeholder"></li>'),
    ]:
        p = parser.parse_listing_page(html, 'https://store.test/list')[0]
        assert p.image_url == 'https://store.test/img.jpg'
        assert (p.current_price, p.original_price) == (300, 600)


@pytest.mark.parametrize('body', ['<html>Verify you are human</html>', '{}', '{"products": {}}', '[]'])
def test_bad_feed_is_not_an_empty_success(body):
    with pytest.raises(ValueError):
        ShopifyParser().parse_listing_page(body, 'https://store.test/products.json')


def test_shopify_page_ten_is_not_a_silent_limit():
    assert ShopifyParser().get_next_page_url('{"products":[{}]}', 'https://store.test/products.json?limit=1&page=10').endswith('page=11')


def test_colors_are_not_sizes():
    item = dict(title='Atomic Skis', handle='skis', options=[{'name':'Color'}], variants=[dict(price='300', compare_at_price='600', option1='Ocean Blue')])
    p = ShopifyParser().parse_listing_page(json.dumps({'products':[item]}), 'https://store.test/products.json')[0]
    assert p.sizes is None


def test_browser_fields_and_invalid_records():
    good = dict(name='Atomic Skis', url='/ski', current_price='300', original_price='600', image_url='//cdn.test/ski.jpg', sizes=['170cm'], brand='Atomic', product_type='Skis')
    raw = [good, {**good, 'current_price':'NaN'}, {**good, 'current_price':'oops'}, {**good, 'url':''}, {**good, 'url':'javascript:alert(1)'}]
    products = _parse_raw_products(raw, 'https://store.test')
    assert len(products) == 1
    assert products[0].sizes == ['170cm']
    assert products[0].brand == 'Atomic'
    assert products[0].image_url == 'https://cdn.test/ski.jpg'
    assert _products_to_deals([Product('Atomic Skis','https://store.test/ski', float('nan'),600)], 'Test') == []


def test_report_lengths_only_apply_to_boards_and_skis():
    deals = _products_to_deals([Product('Atomic Skis', 'https://s.test/ski',300,600), Product('Ski Jacket','https://s.test/jacket',100,200)], 'Test')
    report = build_scrape_report(deals, [StoreConfig('Test','s.test')])
    assert report.missing_lengths == 1 and report.length_eligible == 1
    accepted, withheld = protect_partial_snapshots(deals, {'Test':100}, {'Test':{'errors':1}})
    assert not accepted and withheld == ['Test']
    accepted, withheld = protect_partial_snapshots(deals, {'Test':100}, {'Test':{'errors':0}})
    assert accepted == deals and not withheld


def test_collection_errors_preserve_other_valid_products(monkeypatch):
    async def no_sleep(_): pass
    monkeypatch.setattr('aggregator.scraper.asyncio.sleep', no_sleep)
    async def run():
        item = dict(title='Atomic Skis',handle='ski',variants=[dict(price='300',compare_at_price='600')])
        def handler(request):
            if '/bad/' in str(request.url): return httpx.Response(200,text='<html>Challenge</html>')
            return httpx.Response(200,json={'products':[item]})
        store = StoreConfig('Test','store.test',['https://store.test/collections/bad','https://store.test/collections/skis'],shopify_products_limit=1)
        outcomes = {}
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            deals = await scrape_store(store,client,delay=0,max_pages=1,outcomes=outcomes)
        assert len(deals) == 1
        assert outcomes['Test']['errors'] == 2
        assert [x['status'] for x in outcomes['Test']['collections']] == ['parse_error','page_limit']
    asyncio.run(run())


def test_browser_pagination_fallback_runs_without_explicit_selector():
    from aggregator.browser import _try_next_page
    class Page:
        async def evaluate(self, js):
            return 'https://store.test/catalog?page=2'
        async def goto(self, url, **kwargs):
            self.destination = url
    async def run():
        page = Page()
        assert await _try_next_page(page, None)
        assert page.destination.endswith('page=2')
    asyncio.run(run())


def test_browser_failed_pagination_is_not_reported_as_complete():
    from aggregator.browser import _try_next_page
    class Page:
        async def evaluate(self, js): return 'https://store.test/catalog?page=2'
        async def goto(self, url, **kwargs): raise TimeoutError()
    async def run():
        with pytest.raises(RuntimeError, match='navigation failed'):
            await _try_next_page(Page(), None)
    asyncio.run(run())


def test_filter_counts_exclude_stale_and_historical_rows(tmp_path):
    from datetime import datetime, timedelta
    from aggregator.db import init_db, upsert_deals, get_brands, get_category_counts, count_with_length
    async def run():
        path = tmp_path / 'counts.db'
        await init_db(path)
        deals = _products_to_deals([Product('Atomic Skis','https://s.test/old',100,200,['170cm'],brand='Atomic')], 'Old')
        deals[0].scraped_at = datetime.utcnow() - timedelta(days=4)
        await upsert_deals(deals,path)
        assert await get_brands(path) == []
        assert await get_category_counts(path) == {}
        assert await count_with_length(path) == 0
    asyncio.run(run())
