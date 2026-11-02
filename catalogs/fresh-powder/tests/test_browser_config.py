"""Tests for browser.py store config registry."""

from aggregator.browser import STORE_CONFIGS, _parse_raw_products


def test_all_expected_configs_exist():
    expected = {"backcountry", "thehouse", "bigcommerce",
                "levelnine", "thecircle", "sacredride"}
    assert expected.issubset(set(STORE_CONFIGS.keys()))


def test_aliases():
    assert STORE_CONFIGS["corbetts"] is STORE_CONFIGS["bigcommerce"]
    assert STORE_CONFIGS["peterglenn"] is STORE_CONFIGS["bigcommerce"]
    assert STORE_CONFIGS["alpineshopvt"] is STORE_CONFIGS["bigcommerce"]


def test_config_tuple_shape():
    for name, config in STORE_CONFIGS.items():
        assert len(config) == 3, f"{name} config should be (wait_sel, js, next_sel)"
        wait_sel, js_extract, next_sel = config
        assert isinstance(wait_sel, str) and wait_sel
        assert isinstance(js_extract, str) and js_extract
        assert next_sel is None or isinstance(next_sel, str)


def test_parse_raw_products():
    raw = [
        {"name": "Test Ski", "url": "/product/test", "current_price": 499.99,
         "original_price": 599.99},
        {"name": "", "url": "/bad", "current_price": 100},  # empty name, should be filtered
        {"name": "No Price", "url": "/bad2", "current_price": None},  # no price, filtered
    ]
    products = _parse_raw_products(raw, "https://example.com")
    assert len(products) == 1
    assert products[0].name == "Test Ski"
    assert products[0].url == "https://example.com/product/test"


def test_parse_raw_products_absolute_url():
    raw = [{"name": "Abs URL", "url": "https://store.com/product",
            "current_price": 100, "original_price": None}]
    products = _parse_raw_products(raw, "https://example.com")
    assert products[0].url == "https://store.com/product"


def test_parse_raw_products_recovers_placeholder_name_from_url():
    raw = [{
        "name": "Gearhead Top Pick",
        "url": "https://www.backcountry.com/nordica-speedmachine-j1-ski-boot-2023-girls",
        "current_price": 105.0,
        "original_price": 150.0,
    }]
    products = _parse_raw_products(raw, "https://www.backcountry.com")
    assert products[0].name == "Nordica Speedmachine J1 Ski Boot 2023 Girls"


def test_parse_raw_products_prefixes_model_only_name_from_url_brand():
    raw = [{
        "name": "DX84 Ski",
        "url": "https://www.backcountry.com/kastle-dx84-ski",
        "current_price": 279.5,
        "original_price": 430.0,
    }]
    products = _parse_raw_products(raw, "https://www.backcountry.com")
    assert products[0].name == "Kastle DX84 Ski"
