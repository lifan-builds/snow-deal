"""Regression checks for real offer prices, persistent history and refresh failures."""
import asyncio
import json
from datetime import datetime, timedelta

import aiosqlite
import httpx
import pytest

from aggregator.db import init_db, upsert_deals, query_deals
from aggregator.models import AggregatedDeal
from aggregator.scraper import fetch_listing, scrape_store
from aggregator.config import StoreConfig
from snow_deals.parsers.shopify import ShopifyParser


def test_shopify_price_and_sizes_belong_to_same_available_offer():
    product = {"title": "Atomic Bent Skis", "handle": "bent", "product_type": "Skis",
               "options": [{"name": "Color"}, {"name": "Size"}], "images": [{"src": "https://example.com/bent.jpg"}],
               "variants": [
                   {"price": "100", "compare_at_price": "600", "available": False, "option2": "160cm"},
                   {"price": "550", "compare_at_price": "600", "available": True, "option2": "170cm"},
                   {"price": "300", "compare_at_price": "600", "available": True, "option1": "Green", "option2": "180cm"},
                   {"price": "300", "compare_at_price": "600", "available": True, "option2": "185cm"},
                   {"price": "bad", "compare_at_price": "600", "available": True},
                   {"price": "NaN", "compare_at_price": "600", "available": True},
               ]}
    result = ShopifyParser().parse_listing_page(json.dumps({"products": [product]}), "https://example.com/collections/skis/products.json")
    assert len(result) == 1
    assert result[0].current_price == 300
    assert result[0].sizes == ["180cm", "185cm"]
    assert result[0].image_url == "https://example.com/bent.jpg"
    assert result[0].discount_pct == 50


def test_retry_429_and_respect_long_retry_after(monkeypatch):
    sleeps = []
    async def sleep(seconds): sleeps.append(seconds)
    monkeypatch.setattr("aggregator.scraper.asyncio.sleep", sleep)
    async def run():
        calls = []
        def handler(request):
            calls.append(request)
            return httpx.Response(429, headers={"Retry-After": "7"}) if len(calls) == 1 else httpx.Response(200, json={"products": []})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            assert (await fetch_listing(client, "https://example.com", 2)).status_code == 200
        assert sleeps == [2, 7, 2]
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(429, headers={"Retry-After": "120"}))) as client:
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_listing(client, "https://example.com", 0)
    asyncio.run(run())


def test_empty_filtered_page_does_not_stop_pagination(monkeypatch):
    async def no_sleep(_): pass
    monkeypatch.setattr("aggregator.scraper.asyncio.sleep", no_sleep)
    async def run():
        calls = []
        def handler(request):
            calls.append(str(request.url))
            if len(calls) == 1:
                return httpx.Response(200, json={"products": [{"title":"Sold out", "variants":[{"available":False}]}]})
            return httpx.Response(200, json={"products":[]})
        store = StoreConfig("Test", "example.com", ["https://example.com/collections/skis"], shopify_products_limit=1)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await scrape_store(store, client, delay=0)
        assert len(calls) == 2
        assert "page=2" in calls[1]
    asyncio.run(run())


def make_deal(url, price, at, store="Evo"):
    return AggregatedDeal(None, store, "Atomic Bent 100", url, price, 800, (1-price/800)*100,
                          "skis", "180cm", 180, 180, at)


def test_history_first_seen_and_currency_queries(tmp_path):
    async def run():
        path = tmp_path / "deals.db"
        await init_db(path)
        first = datetime.now() - timedelta(days=1)
        now = datetime.now()
        await upsert_deals([make_deal("https://example.com/old", 500, first)], path)
        await upsert_deals([make_deal("https://example.com/old", 400, now),
                            make_deal("https://example.com/new", 600, now),
                            make_deal("https://example.com/cad", 200, now, "PRFO")], path)
        rows = await query_deals(sort_by="newest", db_path=path)
        old = next(d for d in rows if d.url.endswith("old"))
        assert old.first_seen == first.isoformat()
        assert old.previous_price == 500
        assert rows[-1].url.endswith("old")
        usd = await query_deals(sort_by="price_low", db_path=path)
        assert [d.current_price for d in usd] == [400, 600]
        cad = await query_deals(currency="CAD", max_price=250, db_path=path)
        assert len(cad) == 1 and cad[0].store == "PRFO"
        await init_db(path)
        async with aiosqlite.connect(path) as db:
            assert (await (await db.execute("SELECT COUNT(*) FROM price_history WHERE url LIKE '%/old'")).fetchone())[0] == 2
    asyncio.run(run())


def test_excludes_false_deals_and_recovers_numeric_lengths():
    from aggregator.scraper import _products_to_deals, _is_kids_product
    from aggregator.categorizer import categorize, is_excluded
    from aggregator.reviews import _extract_brand
    from snow_deals.models import Product
    for name in ["Tailgating Grill & Chill Bundle", "Icon Skirt Western Yoke", "Women's Unreality Dress", "Sunbeam Outdoor Steel Fire Pit"]:
        assert is_excluded(name)
        assert categorize(name) is None
    assert _is_kids_product("Patagonia Baby Beanie - Toddlers'")
    assert _extract_brand("Women's Charmeuse Diana Column Skirt") == ""
    assert _extract_brand("Helly Hansen Ski Jacket") == "helly hansen"
    result = _products_to_deals([Product("Atomic Bent Skis", "https://example.com/bent", 300, 600, ["170", "180"])], "Evo")
    assert (result[0].length_min, result[0].length_max) == (170, 180)
    assert _products_to_deals([Product("Atomic Skis", "https://example.com/skis", .01, 600)], "Evo") == []
