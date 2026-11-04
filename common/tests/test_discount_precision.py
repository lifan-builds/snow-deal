"""Price-derived percentages must decide eligibility before display rounding."""
import asyncio
import sqlite3
from datetime import UTC, datetime

import pytest
from aggregator.db import init_db, query_deals, upsert_deals
from aggregator.models import AggregatedDeal
from deal_common.catalog.query import query
from deal_common.models import Product
from deal_common.offers import VariantOffer, discount


@pytest.mark.parametrize("price,reference,expected", [
    (2220.10, 3699, 39.98107596647742),
    (2219.40, 3699, 40),
    (0.18, 0.30, 40),
    (2219.39, 3699, 40.00027034333604),
    (500, None, 0), (500, 0, 0), (500, 500, 0),
    (0, 500, 0), (float("nan"), 500, 0), (500, float("inf"), 0),
])
def test_shared_product_and_offer_keep_price_precision(price, reference, expected):
    assert discount(price, reference) == pytest.approx(expected, abs=1e-12)
    assert Product("Test", "https://test.example", price, reference).discount_pct == pytest.approx(expected, abs=1e-12)
    assert VariantOffer("1", "https://test.example", price, reference).discount_pct == pytest.approx(expected, abs=1e-12)


def offer(key, price, reference, size="M"):
    return {"variant_key": key, "url": f"https://test.example/product?variant={key}",
                "current_price": price, "original_price": reference, "size": size, "options": size,
                "availability": "in_stock", "image_url": None, "reference_basis": "retailer_compare_at"}


def product(name, offers):
    return {"name": name, "url": f"https://test.example/{name}", "brand": "Test",
                "category": "Equipment", "platform": "", "format": "", "offers": offers}


def test_catalog_filter_selection_and_count_use_unrounded_percentage():
    now = datetime.now(UTC)
    sources = [{"name": "Test", "successful_at": now.isoformat(), "products": [
        product("Boundary", [offer("under", 2220.10, 3699), offer("exact", 2219.40, 3699, "L")]),
        product("Higher", [offer("high", 599.6, 1000)]),
        product("BiggerSaving", [offer("low", 5999, 10000)]),
        product("ChooseHigher", [offer("low", 5999, 10000), offer("high", 599.6, 1000)]),
    ]}]
    filters = {"min_discount": 40, "min_reference": 0, "max_price": 0, "page": 1, "size": "M"}
    result = query(sources, filters, now=now)
    assert result["total"] == 3
    assert [card["name"] for card in result["cards"]] == ["ChooseHigher", "Higher", "BiggerSaving"]
    assert result["cards"][0]["offer"]["url"].endswith("variant=high")
    exact = query(sources, {**filters, "size": "L"}, now=now)
    assert exact["total"] == 1
    assert exact["cards"][0]["offer"]["discount"] == 40


@pytest.mark.parametrize("variants", [False, True])
def test_snow_old_snapshot_filters_sorts_counts_and_pages_from_prices(tmp_path, monkeypatch, variants):
    path = tmp_path / "snow.db"
    asyncio.run(init_db(path))
    now = datetime.now(UTC)
    deals = []
    for name, price, reference, image in [
        ("Under", 2220.10, 3699, None), ("Exact", 2219.40, 3699, None),
        ("LowerImage", 5999, 10000, "https://test.example/image.jpg"),
        ("Higher", 599.6, 1000, None),
    ]:
        url = f"https://test.example/{name}"
        deals.append(AggregatedDeal(None, "Test", f"Atomic {name} Skis", url,
            price, reference, 40, "skis", "180", 180, 180, now, image_url=image,
            offers=[VariantOffer("1", url + "?variant=1", price, reference,
                                 size="180", availability="in_stock")] if variants else []))
    asyncio.run(upsert_deals(deals, path))
    # Emulate old published snapshots whose cached percentages were rounded.
    with sqlite3.connect(path) as db:
        db.execute("UPDATE deals SET discount_pct = 40")
        db.execute("UPDATE deal_offers SET discount_pct = 40")
    before = path.read_bytes()
    monkeypatch.setenv("DEALS_DB_READ_ONLY", "true")
    filters = {"db_path": path, "min_discount": 40, "size": "180" if variants else ""}
    result = asyncio.run(query_deals(**filters))
    assert [d.name for d in result] == ["Atomic Higher Skis", "Atomic LowerImage Skis", "Atomic Exact Skis"]
    assert asyncio.run(query_deals(**filters, count_only=True)) == 3
    assert asyncio.run(query_deals(**filters, offset=1, limit=1))[0].name == "Atomic LowerImage Skis"
    assert path.read_bytes() == before


def test_snow_selects_higher_percentage_variant_before_lower_price(tmp_path):
    path = tmp_path / "variants.db"
    asyncio.run(init_db(path))
    url = "https://test.example/skis"
    deal = AggregatedDeal(None, "Test", "Atomic Test Skis", url, 599.9, 1000,
        40, "skis", "180", 180, 180, datetime.now(UTC), offers=[
            VariantOffer("cheap", url + "?variant=cheap", 599.9, 1000, size="180", availability="in_stock"),
            VariantOffer("higher", url + "?variant=higher", 5996, 10000, size="180", availability="in_stock"),
        ])
    asyncio.run(upsert_deals([deal], path))
    selected = asyncio.run(query_deals(db_path=path, size="180", min_discount=40))[0]
    assert selected.current_price == 5996
    assert selected.purchase_url.endswith("variant=higher")
