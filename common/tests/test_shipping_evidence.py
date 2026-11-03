import asyncio
import json
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import UTC, datetime

import httpx
import pytest
from deal_common.catalog.audit import validate_product
from deal_common.catalog.query import query
from deal_common.catalog.refresh import refresh
from deal_common.catalog.storage import read_offer_history, read_sources
from deal_common.catalog.web import create_app
from deal_common.config import RetailerConfig
from deal_common.parsers.harvey import shipping_notice
from deal_common.parsers.shopify import ShopifyParser
from fastapi.testclient import TestClient
from tool_deals.catalog import CATALOG

ORIGIN = "https://www.harveywoodworking.com"


def item(vendor="ESD：Nov.30（Black）"):
    return {"title": "Industrial Dust Processor", "handle": "dust-processor",
            "vendor": vendor, "product_type": "Dust Collector",
            "options": [{"name": "Color"}], "variants": [
                {"id": 1, "option1": "Lunar White", "price": "3500", "compare_at_price": "4000", "available": True},
                {"id": 2, "option1": "Nebula Black", "price": "3000", "compare_at_price": "4000", "available": True},
            ]}


def parse(raw):
    return ShopifyParser().parse_listing_page(json.dumps({"products": [raw]}), ORIGIN + "/collections/all")[0]


def test_shipping_evidence_applies_to_exact_color_and_preserves_offer_facts():
    p = parse(item())
    white, black = p.offers
    assert (white.availability, white.availability_note) == ("in_stock", "")
    assert black.availability == "unknown"
    assert black.availability_note == "Retailer shipping estimate: Nov.30(Black)"
    assert (black.variant_key, black.current_price, black.original_price, black.options) == ("2", 3000, 4000, "Nebula Black")
    assert black.url.endswith("variant=2")


@pytest.mark.parametrize("vendor", ["ESD: Nov. 30", "ESD: Nov. 30 (Red)", "ESD:",
                                    "ESD: Pending (Black/White)", "ESD: Jan. 1 2020 (Black)"])
def test_unresolved_or_past_looking_notice_cannot_confirm_stock(vendor):
    p = parse(item(vendor))
    assert p.offers[1].availability == "unknown"
    assert p.offers[1].availability_note
    if "(Black)" not in vendor:
        assert p.offers[0].availability == "unknown"


@pytest.mark.parametrize("url", ["https://other.example/products/dust-processor",
                                "https://harveywoodworking.com.other.example/products/dust-processor"])
def test_vendor_semantics_are_retailer_scoped(url):
    raw = item()
    assert shipping_notice(raw, raw["variants"][1], url) == ""


def test_unknown_option_metadata_does_not_exempt_a_variant():
    raw = item()
    raw["options"] = [{"name": "Style"}]
    assert all(o.availability == "unknown" for o in parse(raw).offers)
    raw = item()
    raw["variants"][0].pop("option1")
    assert all(o.availability == "unknown" for o in parse(raw).offers)


def test_sold_out_and_unrelated_vendor_behavior_is_preserved():
    raw = item("In Stock")
    raw["variants"][1]["available"] = False
    assert [o.variant_key for o in parse(raw).offers] == ["1"]
    raw = item("Harvey Woodworking")
    assert all(o.availability == "in_stock" and not o.availability_note for o in parse(raw).offers)


def test_independent_endpoint_audit_rejects_an_orderable_delayed_variant():
    source = item()
    raw = deepcopy(source)
    for variant in raw["variants"]:
        variant["options"] = [variant["option1"]]
        variant["price"] = int(float(variant["price"]) * 100)
        variant["compare_at_price"] = int(float(variant["compare_at_price"]) * 100)
    product = parse(source)
    white, black = product.offers
    card = {"name": product.name, "offer": asdict(black)}
    result = validate_product(card, raw, "USD")
    assert result["status"] == "mismatch" and result["checks"]["stock"] is False
    assert all(value for key, value in result["checks"].items() if key != "stock")
    assert result["merchant"]["shipping_notice"]
    assert validate_product({**card, "offer": asdict(white)}, raw, "USD")["status"] == "match"


def test_notice_survives_refresh_storage_filtering_rendering_and_history(tmp_path):
    source = RetailerConfig("Harvey Woodworking", "www.harveywoodworking.com", [ORIGIN + "/collections/all"])
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / "catalog.db"
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"products": [item()]}))
    report = asyncio.run(refresh(catalog, path, delay=0, transport=transport))
    assert report[0]["status"] == "complete"
    rows = read_sources(path, "tools")
    filters = {"min_reference": 200, "min_discount": 0, "max_price": 0, "page": 1}
    result = query(rows, filters)
    assert result["cards"][0]["offer"]["variant_key"] == "2"
    stocked = query(rows, {**filters, "stock": True})
    assert stocked["cards"][0]["offer"]["variant_key"] == "1"
    assert stocked["cards"][0]["offer"]["current_price"] == 3500
    product = rows[0]["products"][0]
    black = product["offers"][1]
    history = read_offer_history(path, "tools", source.name, product, black, now=datetime.now(UTC))
    assert history[0]["availability"] == "unknown"
    assert history[0]["availability_note"] == black["availability_note"]
    with TestClient(create_app(catalog, path)) as client:
        page = client.get("/").text
        assert "Stock unconfirmed" in page and "Retailer shipping estimate" in page
        stocked_page = client.get("/", params={"stock": "true"}).text
        assert "Lunar White" in stocked_page and "Retailer shipping estimate" not in stocked_page
        history_page = client.get("/history", params={
            "source": source.name, "product": product["url"], "variant": "2"})
        assert history_page.status_code == 200
        assert history_page.text.count(black["availability_note"]) == 2
        assert "Unknown" in history_page.text
