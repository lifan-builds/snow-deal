"""Comparison integrity, crawlability and empty-state regression coverage."""
import asyncio
import copy
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from functools import partial

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from aggregator import comparisons, db
from aggregator.models import AggregatedDeal
from aggregator.web import comparison_routes
from aggregator.web.app import create_app


@pytest.fixture
def comparison_db(tmp_path, monkeypatch):
    path = tmp_path / 'comparisons.db'
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    refs = copy.deepcopy(comparisons.REFERENCES)
    for _, ref in refs.values():
        ref['history_since'] = (now - timedelta(days=2)).isoformat()
    monkeypatch.setattr(comparisons, 'REFERENCES', refs)
    monkeypatch.setattr(comparison_routes, 'catalog_summary', partial(comparisons.catalog_summary, db_path=path))
    monkeypatch.setattr(comparison_routes, 'product_detail', partial(comparisons.product_detail, db_path=path))
    monkeypatch.setenv('PUBLIC_MODE', '1')
    monkeypatch.setenv('SITE_URL', 'https://freshpowder.clifan.com')
    p = comparisons.CATALOG[0]
    offers = [AggregatedDeal(id=None, store=f'Test Shop {i}', name=r['title'], url=r['url'],
                current_price=price, original_price=800, discount_pct=40, category=p['category'],
                sizes=sizes, length_min=None, length_max=None, scraped_at=now,
                currency=currency, image_url='https://example.com/ski.jpg')
              for i, (r, price, currency, sizes) in enumerate(zip(p['offers'][:3],
                  [400, 450, 300], ['USD','USD','CAD'], ['160cm, 180cm', None, '170cm']))]

    async def seed():
        await db.init_db(path)
        await db.upsert_deals([replace(o, scraped_at=now-timedelta(days=4), current_price=10) for o in offers], path)
        await db.upsert_deals([replace(o, scraped_at=now-timedelta(days=1), current_price=o.current_price+50) for o in offers], path)
        await db.upsert_deals(offers, path)
    asyncio.run(seed())
    return path, p, offers, now


def test_reviewed_identity_rejects_similar_variants_and_reused_urls():
    p = comparisons.CATALOG[0]
    ref = p['offers'][0]
    assert comparisons.matched_product(ref['title'], ref['url'], p['category']) == p
    for altered in [ref['title'].replace('2026', '2027'), ref['title']+' Women',
                    ref['title']+' with Bindings', ref['title']+' Used',
                    ref['title']+' Wide', ref['title']+' Junior']:
        assert comparisons.matched_product(altered, ref['url'], p['category']) is None
    assert comparisons.matched_product(ref['title'], 'https://unreviewed.example/item', p['category']) is None
    assert comparisons.matched_product(ref['title'], ref['url'], 'ski boots') is None


def test_catalog_has_unique_reviewed_references():
    refs = [r for p in comparisons.CATALOG for r in p['offers']]
    assert len(comparisons.PRODUCTS) == 24
    assert len(refs) == len(comparisons.REFERENCES)
    for p in comparisons.CATALOG:
        assert len(p['offers']) >= 2
        for r in p['offers']:
            assert str(p['year']) in r['title']
            assert r['url'].startswith('https://')


def test_currency_exact_lengths_and_reviewed_history(comparison_db):
    path, p, offers, now = comparison_db
    usd = asyncio.run(comparisons.product_detail(p['slug'], db_path=path))
    assert [o['current_price'] for o in usd['offers']] == [400, 450]
    assert usd['observed_low'] == 400  # excludes old $10 history and CAD $300
    assert len(usd['chart']) == 2
    assert usd['sizes'] == ['160', '180']
    assert usd['unknown_size_count'] == 1
    middle = asyncio.run(comparisons.product_detail(p['slug'], size="170", db_path=path))
    assert middle['offers'] == []  # min/max overlap is not availability
    exact = asyncio.run(comparisons.product_detail(p['slug'], size="180", db_path=path))
    assert len(exact['offers']) == 1
    cad = asyncio.run(comparisons.product_detail(p['slug'], currency='CAD', db_path=path))
    assert cad['observed_low'] == 300
    assert len(cad['offers']) == 1


def test_stale_and_superseded_offers_are_not_current(comparison_db):
    path, p, offers, now = comparison_db
    async def change():
        # A newer store snapshot with another product retires its old offer.
        await db.upsert_deals([replace(offers[0], name='Different product', url='https://example.com/other',
                                      scraped_at=now+timedelta(seconds=1))], path)
        await db.upsert_deals([replace(offers[1], scraped_at=now-timedelta(days=4))], path)
    asyncio.run(change())
    detail = asyncio.run(comparisons.product_detail(p['slug'], db_path=path))
    assert detail['offers'] == []
    assert detail['history']  # useful history remains when offers expire


def test_product_page_schema_links_and_filters(comparison_db):
    path, p, offers, now = comparison_db
    with TestClient(create_app(enable_lifespan=False)) as client:
        response = client.get('/products/'+p['slug'])
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        schema = [json.loads(s.text) for s in soup.select('script[type="application/ld+json"]')]
        product = next(s for s in schema if s['@type'] == 'Product')
        assert product['offers']['lowPrice'] == 400
        assert product['offers']['priceCurrency'] == 'USD'
        assert product['offers']['offerCount'] == 2
        assert 'aggregateRating' not in product and 'availability' not in product['offers']
        assert soup.select_one('link[rel=canonical]')['href'].endswith(p['slug'])
        assert len(soup.select('.offer-row')) == 2
        filtered = BeautifulSoup(client.get('/products/'+p['slug']+'?currency=CAD&size=').text, 'html.parser')
        assert filtered.select_one('meta[name=robots]')['content'] == 'noindex,follow'
        assert 'C$300.00' in filtered.text
        assert client.get('/products/'+p['slug']+'?currency=EUR').status_code == 422
        assert client.get('/products/'+p['slug']+'?size=999').status_code == 422
        assert client.get('/products/not-a-model').status_code == 404
        assert client.get('/brands/not-a-brand').status_code == 404
        assert '/products/'+p['slug'] in client.get('/products').text
        assert '/products/'+p['slug'] in client.get('/brands/atomic').text
        sitemap = client.get('/sitemap.xml').text
        assert '/products/'+p['slug'] in sitemap and '/brands/atomic' in sitemap
        assert client.get('/how-it-works').status_code == 200


def test_expired_product_has_no_current_offer_schema(comparison_db):
    path, p, offers, now = comparison_db
    asyncio.run(db.upsert_deals([replace(o, scraped_at=now-timedelta(days=4)) for o in offers], path))
    with TestClient(create_app(enable_lifespan=False)) as client:
        response = client.get('/products/'+p['slug'])
        assert response.status_code == 200
        soup = BeautifulSoup(response.text, 'html.parser')
        schema = next(json.loads(s.text) for s in soup.select('script[type="application/ld+json"]') if json.loads(s.text)['@type']=='Product')
        assert 'offers' not in schema
        assert 'No recent offers' in soup.text


def test_catalog_cards_link_to_comparison_but_keep_retailer_action(comparison_db):
    from aggregator.web.routes import templates
    path, p, offers, now = comparison_db
    html = templates.env.get_template('partials/_card.html').render(d=offers[0], site_url='https://freshpowder.clifan.com')
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.select_one('h3 a')['href'] == '/products/'+p['slug']
    assert soup.select_one('.share-btn')['data-url'].endswith('/products/'+p['slug'])
    assert soup.select_one('.comparison-card-links a[target=_blank]')['href'] == offers[0].url


def test_wide_sizes_remain_distinct():
    assert comparisons.reported_sizes('156W cm, 160cm Wide, 158cm, 160W, 150-170cm') == ['156W', '158', '160W']
    assert '156' not in comparisons.reported_sizes('156W cm')
