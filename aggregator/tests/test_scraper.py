"""Tests for the scraper module — product-to-deal conversion and kids filtering."""

from datetime import datetime

from aggregator.config import StoreConfig
from aggregator.scraper import build_scrape_report, _is_kids_product, _products_to_deals
from snow_deals.models import Product


def test_kids_filter():
    assert _is_kids_product("Atomic Bent Junior 100") is True
    assert _is_kids_product("Burton Grom Snowboard") is True
    assert _is_kids_product("K2 Youth Skis") is True
    assert _is_kids_product("Atomic Bent 100") is False


def test_products_to_deals():
    products = [
        Product(name="Atomic Bent 100", url="https://example.com/bent",
                current_price=499.99, original_price=599.99),
        Product(name="Burton Grom Kids Snowboard", url="https://example.com/grom",
                current_price=199.99, original_price=249.99),
    ]
    deals = _products_to_deals(products, "TestStore")
    # Kids product should be filtered out
    assert len(deals) == 1
    assert deals[0].name == "Atomic Bent 100"
    assert deals[0].store == "TestStore"
    # "Atomic" is a known ski brand, so brand-matching categorizes it
    assert deals[0].category == "skis"


def test_products_to_deals_recovers_placeholder_name_before_filtering():
    products = [
        Product(name="Gearhead Top Pick",
                url="https://www.backcountry.com/atomic-bent-100-ski-2025",
                current_price=449.99, original_price=599.99),
    ]
    deals = _products_to_deals(products, "Backcountry")
    assert len(deals) == 1
    assert deals[0].name == "Atomic Bent 100 Ski 2025"
    assert deals[0].category == "skis"


def test_scrape_report_tracks_zero_count_and_missing_fields():
    stores = [
        StoreConfig("Store A", "a.example"),
        StoreConfig("Store B", "b.example"),
    ]
    deals = [
        _products_to_deals([
            Product(name="Atomic Bent 100 Skis", url="https://a.example/bent",
                    current_price=499.99, original_price=599.99),
        ], "Store A")[0],
    ]
    report = build_scrape_report(deals, stores)
    assert report.total_deals == 1
    assert report.stores_with_deals == 1
    assert report.zero_count_stores == ["Store B"]
    assert report.missing_image == 1
    assert report.missing_sizes == 1
