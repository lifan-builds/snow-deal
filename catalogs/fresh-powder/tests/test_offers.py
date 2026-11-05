"""End-to-end offer selection: real size, price, history, and pagination agree."""
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from functools import partial

from fastapi.testclient import TestClient

from deal_common.parsers.shopify import ShopifyParser
from aggregator.scraper import _products_to_deals, build_scrape_report
from aggregator.config import StoreConfig
from aggregator.db import init_db, upsert_deals, query_deals
from aggregator.models import AggregatedDeal
from aggregator.sizes import matches_length


def products(variants=None, handle='ski'):
    variants = variants if variants is not None else [
        dict(id=11, price='200', compare_at_price='1000', available=True, option1='160', option2='Red'),
        dict(id=12, price='400', compare_at_price='1000', available=True, option1='180', option2='Blue'),
        dict(id=13, price='50', compare_at_price='1000', available=False, option1='170', option2='Red'),
        dict(id=14, price='100', compare_at_price='1000', option1='175', option2='Red'),
    ]
    return ShopifyParser().parse_listing_page(json.dumps({'products': [{
        'title':'Atomic Test Skis 2025', 'handle':handle, 'vendor':'Atomic', 'product_type':'Skis',
        'options':[{'name':'Size'}, {'name':'Color'}], 'variants':variants,
    }]}), 'https://shop.test/en-us/collections/sale/products.json?currency=USD')


def setup_db(tmp_path, variants=None):
    path = tmp_path / 'offers.db'
    asyncio.run(init_db(path))
    deals = _products_to_deals(products(variants), 'Test')
    asyncio.run(upsert_deals(deals, path))
    return path, deals


def query(path, **kwargs):
    return asyncio.run(query_deals(db_path=path, **kwargs))


def test_missing_availability_is_unknown_and_sold_out_is_not_selectable():
    item = products()[0]
    assert len(item.offers) == 3
    assert {o.variant_key:o.availability for o in item.offers} == {'11':'in_stock','12':'in_stock','14':'unknown'}
    assert item.offers[0].size == '160'
    assert item.offers[0].options == '160 / Red'
    assert 'currency=USD&variant=11' in item.offers[0].url


def test_coverage_distinguishes_variant_count_from_confirmed_sizes():
    deals = _products_to_deals(products(), 'Test')
    unknown = _products_to_deals(products([
        dict(id=99, price='200', compare_at_price='600', option1='180')
    ], handle='unknown'), 'Test')
    report = build_scrape_report(deals + unknown, [StoreConfig('Test', 'shop.test')])
    assert (report.total_deals, report.variant_offers, report.deals_with_variants,
            report.confirmed_size_deals) == (2, 4, 2, 1)
    assert report.store_summaries[0].confirmed_size_deals == 1


def test_size_selects_its_price_discount_and_url_before_count_and_sort(tmp_path):
    path, _ = setup_db(tmp_path)
    best = query(path)[0]
    assert (best.current_price, best.discount_pct, best.availability) == (100, 90, 'unknown')
    selected = query(path, size='180cm')[0]
    assert (selected.current_price, selected.original_price, selected.discount_pct) == (400,1000,60)
    assert selected.sizes == '180' and selected.offer_options == '180 / Blue'
    assert selected.variant_key == '12'
    assert selected.url.endswith('/ski?currency=USD')
    assert selected.purchase_url.endswith('currency=USD&variant=12')
    assert query(path, size='180', min_discount=70) == []
    assert query(path, size='170', count_only=True) == 0
    assert query(path, size='175') == []  # Unknown is not confirmed stock.
    assert query(path, size='180', count_only=True) == 1


def test_budget_can_select_a_different_variant_not_discard_whole_product(tmp_path):
    path, _ = setup_db(tmp_path, [
        dict(id=1,price='600',compare_at_price='2000',available=True,option1='160'),
        dict(id=2,price='300',compare_at_price='600',available=True,option1='180'),
    ])
    assert query(path)[0].current_price == 600  # Greatest percentage, not cheapest.
    assert query(path, max_price=350)[0].current_price == 300
    assert query(path, max_price=350, min_reference=1000) == []
    assert query(path, min_reference=1000)[0].discount_pct == 70


def test_length_range_never_invents_intermediate_size(tmp_path):
    path, _ = setup_db(tmp_path)
    assert query(path, size_min=168, size_max=172) == []
    assert query(path, size_min=179, size_max=185)[0].current_price == 400
    assert matches_length('160cm, 180cm', 165,175) is False
    assert matches_length('160-180cm', 165,175) is False
    assert matches_length('161W',160,165) is True
    assert matches_length('110mm',100,120) is False


def test_variant_history_does_not_compare_different_sizes(tmp_path):
    path, deals = setup_db(tmp_path)
    deals[0].scraped_at -= timedelta(hours=1)
    asyncio.run(upsert_deals(deals, path))
    changed = _products_to_deals(products([
        dict(id=11,price='180',compare_at_price='1000',available=True,option1='160'),
        dict(id=12,price='350',compare_at_price='1000',available=True,option1='180'),
    ]), 'Test')
    asyncio.run(upsert_deals(changed, path))
    selected = query(path, size='180')[0]
    assert selected.previous_price == 400
    assert selected.current_price == 350
    assert query(path, size='175') == []


def test_unknown_legacy_offers_remain_browseable_but_not_confirmed_size_matches(tmp_path):
    path = tmp_path/'legacy.db'
    asyncio.run(init_db(path))
    deal = AggregatedDeal(None,'Test','Legacy Skis 2017','https://shop.test/legacy',100,500,80,
                          'skis','160cm, 180cm',160,180,datetime.now(timezone.utc).replace(tzinfo=None))
    asyncio.run(upsert_deals([deal],path))
    assert query(path)[0].availability == 'unknown'
    assert query(path)[0].variant_key is None
    assert query(path,size='160') == []
    assert query(path,size_min=165,size_max=175) == []
    assert query(path,size_min=180)[0].model_label == 'Model 2017'


def test_variant_history_does_not_cross_product_reuse(tmp_path):
    path, deals = setup_db(tmp_path)
    deals[0].scraped_at -= timedelta(hours=1)
    asyncio.run(upsert_deals(deals, path))
    replacement = _products_to_deals(products(), 'Test')
    replacement[0].name = 'Different Model Skis 2026'
    asyncio.run(upsert_deals(replacement, path))
    assert query(path, size='180')[0].previous_price is None


def test_year_filter_preserves_discount_order_and_excludes_unknown_years(tmp_path):
    path, deals = setup_db(tmp_path)
    items = []
    for index, name in enumerate(['Legacy Skis 00 - 01', 'Undated Skis', 'Modern Skis 2026']):
        item = _products_to_deals(products(handle=f'year-{index}'), 'Test')[0]
        item.name = name
        item.scraped_at = deals[0].scraped_at
        items.append(item)
    asyncio.run(upsert_deals(items, path))
    assert query(path, count_only=True) == 4
    assert query(path, year_from=2025, count_only=True) == 2
    assert query(path, year_from=2026)[0].name == 'Modern Skis 2026'
    assert query(path, year_from=2027) == []


def test_observed_aspen_feed_preserves_real_variant_identity_and_size(tmp_path):
    fixture = Path(__file__).parent/'fixtures/aspen_variant_sample.json'
    parsed = ShopifyParser().parse_listing_page(fixture.read_text(),
        'https://www.aspenskiandboard.com/collections/skis/products.json?limit=24&page=1')
    deals = _products_to_deals(parsed, 'Aspen Ski and Board')
    path = tmp_path/'observed.db'
    asyncio.run(init_db(path))
    asyncio.run(upsert_deals(deals, path))
    selected = query(path, size='146')[0]
    assert selected.name.startswith('Atomic Maverick 78')
    assert (selected.current_price, selected.original_price) == (329.95, 550)
    assert selected.purchase_url.endswith('?variant=52267419336992')
    assert selected.offer_options == 'Grey/Black / 146cm'
    assert selected.availability == 'in_stock'
    assert query(path, size='150') == []


def test_size_selection_orders_matching_offers_before_pagination(tmp_path):
    path, _ = setup_db(tmp_path)
    more = _products_to_deals(products([dict(id=21,price='300',compare_at_price='1000',available=True,option1='180')], 'other'), 'Test')
    # All products in one snapshot share a time.
    original = _products_to_deals(products(), 'Test')
    for d in more+original:
        d.scraped_at = more[0].scraped_at
    asyncio.run(upsert_deals(more+original,path))
    assert query(path,size='180',limit=1)[0].current_price == 300
    assert query(path,size='180',limit=1,offset=1)[0].current_price == 400
    assert query(path,size='180',count_only=True) == 2


def test_size_filter_full_page_partial_and_pagination_agree(tmp_path, monkeypatch):
    import aggregator.web.routes as routes
    import aggregator.web.app as app
    import aggregator.db as db
    path, _ = setup_db(tmp_path)
    monkeypatch.setenv('PUBLIC_MODE','1')
    monkeypatch.setenv('DISABLE_APP_LIFESPAN','1')
    for name in ('query_deals','get_brands','get_category_counts','count_with_length','store_status'):
        monkeypatch.setattr(routes,name,partial(getattr(db,name),db_path=path))
    with TestClient(app.create_app()) as client:
        for prefix in ('/', '/deals'):
            response=client.get(prefix+'?size=180&min_reference=500')
            assert response.status_code==200
            assert '$400.00' in response.text and '60% OFF' in response.text
            assert 'variant=12' in response.text and 'Reported in stock' in response.text
            assert 'Variant 12 · 180 / Blue.' in response.text
            assert 'Exact variant not supplied' not in response.text
            assert 'Save $600.00' in response.text and 'vs retailer reference' in response.text
            assert '$100.00' not in response.text
        assert client.get('/deals?size=175').status_code==200
        assert 'No deals match' in client.get('/deals?size=175').text
        assert client.get('/?min_reference=-1').status_code==422
        assert 'No deals match' in client.get('/deals?year_from=2026').text
        assert '$400.00' in client.get('/?year_from=2025&size=180').text
        assert client.get('/?year_from=1800').status_code == 422


def test_skiessentials_exact_options_survive_storage_and_filtering(tmp_path):
    from deal_common.parsers.skiessentials import _product

    fixture = Path(__file__).resolve().parents[3] / 'common/tests/fixtures/skiessentials-xo.json'
    product = _product(json.loads(fixture.read_text()))
    deals = _products_to_deals([product], 'Ski Essentials')
    path = tmp_path / 'skiessentials.db'
    asyncio.run(init_db(path))
    asyncio.run(upsert_deals(deals, path))
    assert query(path, size='172', count_only=True) == 0
    selected = query(path, size='178', min_discount=80, max_price=200)[0]
    assert selected.variant_key == '47335044710696'
    assert selected.current_price == 199 and selected.original_price == 1250
    assert selected.availability == 'in_stock' and selected.sizes == '178'
    assert selected.purchase_url.endswith('?ski+size=178')
    assert '?' not in selected.url
    assert query(path, size='178', min_discount=85, count_only=True) == 0


def test_skiessentials_uses_exact_offer_parser():
    from aggregator.config import STORES
    from aggregator.scraper import _get_parser
    from deal_common.parsers.skiessentials import SkiEssentialsParser

    source = next(s for s in STORES if s.name == 'Ski Essentials')
    assert not source.use_browser
    assert isinstance(_get_parser(source.parser_type), SkiEssentialsParser)
    assert len(source.scrape_urls) == 6


def test_equal_percentage_variant_prefers_cash_savings_before_price(tmp_path):
    path, deals = setup_db(tmp_path, [
        {'id': 1, 'price': '300', 'compare_at_price': '600', 'available': True, 'option1': '160'},
        {'id': 2, 'price': '1000', 'compare_at_price': '2000', 'available': True, 'option1': '180'},
    ])
    assert (deals[0].current_price, deals[0].original_price, deals[0].sizes) == (1000, 2000, '180cm')
    selected = query(path)[0]
    assert (selected.variant_key, selected.current_price, selected.discount_pct) == ('2', 1000, 50)
    assert selected.purchase_url.endswith('&variant=2')
    budget = query(path, max_price=350)[0]
    assert (budget.variant_key, budget.current_price, budget.sizes) == ('1', 300, '160')
    assert budget.purchase_url.endswith('&variant=1')
    assert query(path, min_reference=1000, count_only=True) == 1
    assert query(path, min_reference=1000)[0].variant_key == '2'
    assert query(path, size='160', min_reference=1000) == []


def test_exact_percentage_stays_ahead_of_cash_savings_for_variants(tmp_path):
    path, deals = setup_db(tmp_path, [
        {'id': 1, 'price': '49.99', 'compare_at_price': '100', 'available': True, 'option1': '160'},
        {'id': 2, 'price': '1000', 'compare_at_price': '2000', 'available': True, 'option1': '180'},
    ])
    assert deals[0].current_price == 49.99
    selected = query(path)[0]
    assert (selected.variant_key, selected.discount_pct) == ('1', 50.01)
    assert selected.purchase_url.endswith('&variant=1')


def test_default_cash_savings_order_precedes_images_with_stable_pagination(tmp_path):
    path = tmp_path / 'savings-order.db'
    asyncio.run(init_db(path))
    deals = []
    for handle, price, reference, image, legacy in [
        ('small-variant', '300', '600', 'https://cdn.test/small.jpg', False),
        ('large-variant', '1000', '2000', None, False),
        ('small-legacy', '200', '400', 'https://cdn.test/legacy.jpg', True),
        ('large-legacy', '750', '1500', None, True),
        ('precise-variant', '49.99', '100', None, False),
    ]:
        item = products([
            {'id': 1, 'price': price, 'compare_at_price': reference, 'available': True, 'option1': '180'},
        ], handle=handle)[0]
        item.image_url = image
        for offer in item.offers:
            offer.image_url = image
        if legacy:
            item.offers = []
        deals.extend(_products_to_deals([item], 'Test'))
    for deal in deals:
        deal.scraped_at = deals[0].scraped_at
    asyncio.run(upsert_deals(deals, path))
    expected = ['precise-variant', 'large-variant', 'large-legacy', 'small-variant', 'small-legacy']
    actual = [deal.url.split('/')[-1].split('?')[0] for deal in query(path)]
    assert actual == expected
    pages = [query(path, limit=2, offset=offset) for offset in (0, 2, 4)]
    assert [deal.url for page in pages for deal in page] == [deal.url for deal in query(path)]
    assert query(path, count_only=True) == 5
    assert pages[0][1].purchase_url.endswith('&variant=1')
    assert query(path, sort_by='price_low')[0].current_price == 49.99
    assert query(path, sort_by='price_high')[0].current_price == 1000


def test_default_savings_order_groups_currencies_after_exact_percentage(tmp_path):
    path = tmp_path / 'currency-savings.db'
    asyncio.run(init_db(path))
    deals = []
    for handle, price, reference, currency in [
        ('cad-large', '10000', '20000', 'CAD'),
        ('usd-small', '200', '400', 'USD'),
        ('cad-small', '300', '600', 'CAD'),
        ('usd-large', '1000', '2000', 'USD'),
        ('cad-precise', '49.99', '100', 'CAD'),
    ]:
        item = products([
            {'id': 1, 'price': price, 'compare_at_price': reference, 'available': True, 'option1': '180'},
        ], handle=handle)[0]
        deal = _products_to_deals([item], f'Test {currency}')[0]
        deal.currency = currency
        deals.append(deal)
    for deal in deals:
        deal.scraped_at = deals[0].scraped_at
    asyncio.run(upsert_deals(deals, path))

    def handles(**kwargs):
        return [deal.url.split('/')[-1].split('?')[0] for deal in query(path, **kwargs)]

    assert handles() == ['cad-precise', 'usd-large', 'usd-small', 'cad-large', 'cad-small']
    assert handles(currency='CAD') == ['cad-precise', 'cad-large', 'cad-small']
    assert handles(currency='USD') == ['usd-large', 'usd-small']
    assert handles(sort_by='invalid') == handles()
    assert query(path, currency='USD', count_only=True) == 2
    assert query(path, currency='CAD', count_only=True) == 3
