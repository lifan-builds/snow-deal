import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from cycling_deals.catalog import CATALOG as CYCLING
from tool_deals.catalog import CATALOG as TOOLS
from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize, refresh
from deal_common.catalog.storage import read_sources, save_source
from deal_common.catalog.web import create_app
from deal_common.config import RetailerConfig
from deal_common.models import Product
from deal_common.offers import VariantOffer

NOW = datetime(2026, 11, 2, 12, tzinfo=timezone.utc)


def offer(key="1", price=500, reference=2000, size="M", stock="in_stock"):
    return dict(variant_key=key, url=f"https://example.com/products/bike?variant={key}",
                current_price=price, original_price=reference, size=size, options=size,
                availability=stock, image_url=None, reference_basis="retailer_compare_at")


def product(name="Test Mountain Bike", offers=None):
    return dict(name=name, url="https://example.com/products/" + name,
                brand="Test", category="Mountain bikes", format="", platform="",
                offers=offers or [offer()])


def source(products, timestamp=NOW):
    return dict(name="BikesOnline", successful_at=timestamp.isoformat(), products=products,
                checked_at=timestamp.isoformat(), status="complete", detail={})


def filters(**overrides):
    return dict(min_discount=0, min_reference=0, max_price=0, page=1, **overrides)


def test_size_selects_one_real_offer_before_ranking_count_and_pagination():
    a = product("A", [offer("a-cheap", 200, 2000, "S"), offer("a-medium", 1500, 2000, "M")])
    b = product("B", [offer("b-medium", 800, 2000, "Medium")])
    unknown = product("Unknown", [offer("unknown", 100, 2000, "M", "unknown")])
    result = query([source([a, b, unknown])], filters(size="M"), now=NOW)
    assert result["total"] == 2
    assert [p["name"] for p in result["cards"]] == ["B", "A"]
    assert result["cards"][1]["offer"]["current_price"] == 1500
    assert result["cards"][1]["offer"]["url"].endswith("a-medium")
    strict = {**filters(size="M"), "min_discount": 50, "max_price": 1000}
    assert query([source([a, b, unknown])], strict, now=NOW)["total"] == 1


def test_reference_floor_and_budget_apply_to_same_variant():
    p = product(offers=[offer("big", 1500, 3000), offer("small", 200, 500)])
    f = {**filters(), "min_reference": 2000, "max_price": 1000}
    assert query([source([p])], f, now=NOW)["total"] == 0


@pytest.mark.parametrize("label,requested", [("SM", "S"), ("MD", "Medium"), ("LG", "L")])
def test_retailer_size_abbreviations_match_without_splitting_compound_sizes(label, requested):
    exact = product("Exact", [offer("exact", 1000, 2000, label)])
    compound = product("Compound", [offer("compound", 500, 2000, "S/M/L")])
    result = query([source([exact, compound])], filters(size=requested), now=NOW)
    assert [p["name"] for p in result["cards"]] == ["Exact"]
    assert result["cards"][0]["offer"]["size"] == label


def test_percent_wins_over_savings_and_image_then_page_is_stable():
    products = [product(f"P{i:02}", [offer(str(i), 2000 + i, 10000)]) for i in range(30)]
    products.append(product("Largest discount", [offer("deep", 10, 100)]))
    result = query([source(products)], filters(), now=NOW)
    assert result["cards"][0]["name"] == "Largest discount"
    assert result["total"] == 31 and len(result["cards"]) == 24
    page2 = query([source(products)], {**filters(), "page": 2}, now=NOW)
    assert len(page2["cards"]) == 7
    assert not ({p["name"] for p in result["cards"]} & {p["name"] for p in page2["cards"]})


def test_stale_future_and_unknown_stock():
    for timestamp in (NOW - timedelta(hours=25), NOW + timedelta(minutes=1)):
        assert query([source([product()], timestamp)], filters(), now=NOW)["total"] == 0
    row = source([product(offers=[offer(stock="unknown")])])
    assert query([row], filters(), now=NOW)["total"] == 1
    assert query([row], filters(stock=True), now=NOW)["total"] == 0


def test_atomic_source_history_retained_on_failure_and_cleared_by_empty(tmp_path):
    db = tmp_path / "cycling.db"
    save_source(db, "cycling", "BikesOnline", NOW.isoformat(), [product()], "complete", {})
    later = (NOW + timedelta(hours=1)).isoformat()
    save_source(db, "cycling", "BikesOnline", later, [], "incomplete", {"errors": 1})
    row = read_sources(db, "cycling")[0]
    assert row["successful_at"] == NOW.isoformat() and row["checked_at"] == later
    assert len(row["products"]) == 1
    with pytest.raises(ValueError, match="different catalog"):
        read_sources(db, "tools")
    save_source(db, "cycling", "BikesOnline", later, [], "complete", {})
    assert read_sources(db, "cycling")[0]["products"] == []


@pytest.mark.parametrize("mode", ["malformed", "truncated", "currency", "forbidden"])
def test_refresh_failures_do_not_renew_or_remove_previous_data(tmp_path, mode):
    db = tmp_path / "test.db"
    save_source(db, "cycling", "Example", NOW.isoformat(), [product()], "complete", {})
    config = RetailerConfig("Example", "example.com", ["https://example.com/collections/sale"],
                            shopify_products_limit=1, verify_shopify_currency=(mode == "currency"))
    def handler(request):
        if mode == "forbidden":
            return httpx.Response(403)
        if mode == "currency":
            return httpx.Response(200, text='Shopify.currency = {"active":"CAD"};')
        if mode == "malformed":
            return httpx.Response(200, json={"error": "not inventory"})
        return httpx.Response(200, json={"products": [{"title": "Full price"}]})
    report = asyncio.run(refresh(replace(CYCLING, sources=(config,)), db, max_pages=1,
                                 delay=0, transport=httpx.MockTransport(handler)))
    assert report[0]["status"] == "incomplete"
    row = read_sources(db, "cycling")[0]
    assert row["successful_at"] == NOW.isoformat() and len(row["products"]) == 1


def test_real_parser_refresh_to_web_variant_flow(tmp_path):
    config = RetailerConfig("BikesOnline", "example.com", ["https://example.com/collections/sale"])
    catalog = replace(CYCLING, sources=(config,))
    payload = {"products": [{"title": "A Mountain Bike", "handle": "bike", "product_type": "Mountain Bikes",
        "vendor": "A", "options": [{"name": "Size"}], "variants": [
            {"id": 1, "available": True, "price": "100", "compare_at_price": "2000", "option1": "S"},
            {"id": 2, "available": True, "price": "1200", "compare_at_price": "2000", "option1": "M"}]}]}
    db = tmp_path / "cycling.db"
    asyncio.run(refresh(catalog, db, delay=0, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload))))
    client = TestClient(create_app(catalog, db))
    page = client.get("/?size=M")
    assert page.status_code == 200
    assert "$1,200" in page.text and "−40.0" in page.text
    assert "?variant=2" in page.text and "?variant=1" not in page.text
    assert client.get("/healthz").json()["status"] == "ready"


@pytest.mark.parametrize("catalog", [CYCLING, TOOLS])
def test_empty_read_only_sites_assets_validation_and_escaping(tmp_path, catalog):
    db = tmp_path / "absent.db"
    client = TestClient(create_app(catalog, db))
    assert client.get("/").status_code == 200
    assert not db.exists()
    assert "Fresh deals are on their way" in client.get("/").text
    assert catalog.name in client.get("/sources").text
    assert client.get("/static/catalog.css").status_code == 200
    assert client.get("/static/catalog.js").status_code == 200
    assert client.get("/brand/hero.svg").status_code == 200
    assert client.get("/brand/brand.css").status_code == 200
    for bad in ("min_discount=-1", "min_reference=nan", "max_price=inf", "page=0"):
        assert client.get("/?" + bad).status_code == 422
    page = client.get("/", params={"q": '<script>alert("x")</script>'})
    assert '<script>alert("x")</script>' not in page.text
    assert "noindex" in page.headers["X-Robots-Tag"]


def test_normalize_rejects_external_links_nonfinite_and_unsafe_images():
    p = Product("Mountain Bike", "https://example.com/products/bike", 500, 2000,
                product_type="Mountain Bikes", offers=[VariantOffer(**offer())])
    assert len(normalize([p], CYCLING, "example.com")) == 1
    p.offers[0].url = "https://example.com.evil.test/"
    assert normalize([p], CYCLING, "example.com") == []
    p.offers[0] = VariantOffer(**offer(price=float("nan")))
    assert normalize([p], CYCLING, "example.com") == []
    p.offers[0] = VariantOffer(**{**offer(), "image_url": "javascript:alert(1)"})
    assert normalize([p], CYCLING, "example.com")[0]["offers"][0]["image_url"] is None


def test_frame_size_does_not_include_wheel_size_or_guess_unknown_option():
    import json
    from deal_common.parsers.shopify import ShopifyParser
    parser = ShopifyParser(size_option_names=CYCLING.size_option_names)
    item = {"title": "Mountain Bike", "handle": "bike", "options": [
        {"name": "Wheel Size"}, {"name": "Frame Size"}], "variants": [
        {"id": 1, "available": True, "price": "900", "compare_at_price": "2000",
         "option1": "29 inch", "option2": "M"}]}
    parsed = parser.parse_listing_page(json.dumps({"products": [item]}), "https://example.com/collections/sale")
    selected = parsed[0].offers[0]
    assert selected.size == "M"
    assert selected.options == "29 inch / M"
    assert selected.url.endswith("variant=1")
    item["options"] = [{"name": "Wheel Size"}]
    assert parser.parse_listing_page(json.dumps({"products": [item]}), "https://example.com/collections/sale")[0].offers[0].size is None
    item.pop("options")
    assert parser.parse_listing_page(json.dumps({"products": [item]}), "https://example.com/collections/sale")[0].offers[0].size is None


def test_removing_reference_filter_does_not_silently_reapply_default(tmp_path):
    from bs4 import BeautifulSoup
    from urllib.parse import parse_qs, urlsplit
    client = TestClient(create_app(CYCLING, tmp_path / "empty.db"))
    page = BeautifulSoup(client.get("/?size=M&stock=true&page=3").text, "html.parser")
    link = page.select_one('a[aria-label="Remove filter: Reference ≥ $ 1000"]')
    params = parse_qs(urlsplit(link["href"]).query)
    assert params["min_reference"] == ["0"]
    assert params["size"] == ["M"] and params["stock"] == ["true"] and params["page"] == ["1"]
    stock = page.select_one('a[aria-label="Remove filter: Reported in stock"]')
    assert parse_qs(urlsplit(stock["href"]).query)["stock"] == ["false"]


def test_normalize_rejects_wrong_product_or_variant_purchase_destination():
    p = Product("Mountain Bike", "https://example.com/products/bike", 500, 2000,
                product_type="Mountain Bikes", offers=[VariantOffer(**offer())])
    for url in ("https://example.com/products/another-bike?variant=1",
                "https://example.com/products/bike?variant=2",
                "https://example.com/products/bike"):
        p.offers[0].url = url
        assert normalize([p], CYCLING, "example.com") == []


def test_history_never_combines_variants_identity_or_multiple_days(tmp_path):
    from deal_common.catalog.storage import read_offer_history
    db = tmp_path / "history.db"
    current = product("Bike", [offer("one", 1000, 2000), offer("two", 1500, 2000)])
    save_source(db, "cycling", "BikesOnline", (NOW - timedelta(days=1)).isoformat(), [current], "complete", {})
    current["offers"][0]["current_price"] = 900
    save_source(db, "cycling", "BikesOnline", (NOW - timedelta(hours=23)).isoformat(), [current], "complete", {})
    changed = {**current, "name": "Different build"}
    save_source(db, "cycling", "BikesOnline", (NOW - timedelta(hours=1)).isoformat(), [changed], "complete", {})
    save_source(db, "cycling", "BikesOnline", NOW.isoformat(), [], "incomplete", {})
    rows = read_offer_history(db, "cycling", "BikesOnline", current, current["offers"][0], now=NOW)
    assert len(rows) == 1 and rows[0]["price"] == 900
    assert rows[0]["observed_at"] != NOW.isoformat()
    current["offers"][0]["options"] = "Different package"
    assert read_offer_history(db, "cycling", "BikesOnline", current, current["offers"][0], now=NOW) == []


def test_history_route_scoped_to_configured_source_and_current_variant(tmp_path):
    db = tmp_path / "history.db"
    p = product()
    save_source(db, "cycling", "BikesOnline", datetime.now(timezone.utc).isoformat(), [p], "complete", {})
    client = TestClient(create_app(CYCLING, db))
    params = dict(source="BikesOnline", product=p["url"], variant="1")
    page = client.get("/history", params=params)
    assert page.status_code == 200 and "1 observed day" in page.text and "Still collecting history" in page.text
    assert client.get("/history", params={**params, "variant": "not-this-variant"}).status_code == 404
    assert client.get("/history", params={**params, "source": "Unconfigured"}).status_code == 404


@pytest.mark.parametrize("old_brand", ["In Stock", "Out of Stock", "ESD：Nov.30（Black）"])
def test_history_survives_fulfillment_label_cleanup_without_rewriting_evidence(tmp_path, old_brand):
    from deal_common.catalog.storage import read_offer_history
    db = tmp_path / "history.db"
    previous = {**product(offers=[offer(price=1200, stock="unknown")]), "brand": old_brand}
    current = {**product(offers=[offer(price=1100)]), "brand": "Unspecified"}
    previous_time = (NOW - timedelta(days=1)).isoformat()
    save_source(db, "cycling", "BikesOnline", previous_time, [previous], "complete", {})
    save_source(db, "cycling", "BikesOnline", NOW.isoformat(), [current], "complete", {})
    original_bytes = db.read_bytes()
    history = read_offer_history(db, "cycling", "BikesOnline", current, current["offers"][0], now=NOW)
    assert len(history) == 2
    assert history[1] == {"observed_at": previous_time, "price": 1200,
                          "reference": 2000, "availability": "unknown", "availability_note": "", "price_note": ""}
    assert history[0]["price"] == 1100
    assert db.read_bytes() == original_bytes


@pytest.mark.parametrize("level,field,value", [
    ("product", "brand", "Real Manufacturer"),
    ("product", "name", "Different build"),
    ("product", "url", "https://example.com/products/other-model"),
    ("offer", "variant_key", "different-variant"),
    ("offer", "options", "Different package"),
    ("offer", "url", "https://example.com/products/bike?variant=different"),
])
def test_history_label_cleanup_cannot_merge_other_product_or_variant(tmp_path, level, field, value):
    from deal_common.catalog.storage import read_offer_history
    db = tmp_path / "history.db"
    previous = {**product(), "brand": "In Stock"}
    current = {**product(), "brand": "Unspecified"}
    (previous if level == "product" else previous["offers"][0])[field] = value
    save_source(db, "cycling", "BikesOnline", NOW.isoformat(), [previous], "complete", {})
    assert read_offer_history(db, "cycling", "BikesOnline", current, current["offers"][0], now=NOW) == []


def test_frameset_keyword_cannot_override_accessory_taxonomy():
    p = Product("Frameset transport bag", "https://example.com/products/bag", 100, 200,
                product_type="Bike Bags")
    assert CYCLING.classify(p) is None


def test_daily_history_retention_is_bounded_and_failed_checks_do_not_replace_it(tmp_path):
    from deal_common.catalog.storage import database
    db = tmp_path / 'history.db'
    for timestamp in (NOW-timedelta(days=46), NOW-timedelta(days=1), NOW-timedelta(hours=1), NOW):
        save_source(db, 'cycling', 'BikesOnline', timestamp.isoformat(), [product()], 'complete', {})
    save_source(db, 'cycling', 'BikesOnline', (NOW+timedelta(hours=1)).isoformat(), [], 'incomplete', {})
    with database(db, 'cycling') as connection:
        observations = [r[0] for r in connection.execute('SELECT observed_at FROM observations ORDER BY observed_at')]
    assert observations == [(NOW-timedelta(days=1)).isoformat(), NOW.isoformat()]


@pytest.mark.parametrize("name", [
    "Festool Granat P40 Grit Abrasives for LRS 400 Sander, Pack of 50 497157",
    "Festool Granat P280 Grit Abrasives for LRS 400 Sander, Pack of 50 497203",
    "Sanding discs for random orbit sander",
])
def test_named_machine_does_not_turn_replacement_abrasives_into_power_tools(name):
    assert TOOLS.classify(Product(name=name, url="https://example.com/item", current_price=49,
                                 original_price=249, product_type="Power Tools")) is None


def test_complete_sander_with_included_abrasives_remains_a_power_tool():
    item = Product(name="Random orbit sander kit with abrasives", url="https://example.com/item",
                   current_price=149, original_price=249, product_type="Power Tools")
    assert TOOLS.classify(item).category == "Power tools"


def test_explicit_frameset_tag_precedes_generic_mountain_bike_taxonomy():
    item = Product(name="OPEN ONE+ Frame", url="https://example.com/item", current_price=1299,
                   original_price=3499, product_type="Mountain Bikes", tags=("Frameset", "Mountain Bikes"))
    assert CYCLING.classify(item).category == "Framesets"
    assert CYCLING.classify(replace(item, product_type="Bike Parts")) is None


def test_numeric_s_frame_size_stays_distinct_from_plain_numeric_size():
    import json
    from deal_common.parsers.shopify import ShopifyParser
    parser = ShopifyParser(size_option_names=CYCLING.size_option_names,
                           size_value_pattern=CYCLING.size_value_pattern)
    raw = {"handle": "compact-frame", "title": "Compact Frameset", "product_type": "Framesets",
           "options": [{"name": "Color"}, {"name": "Size"}],
           "variants": [{"id": 1, "available": True, "price": "1000", "compare_at_price": "3000",
                         "option1": "Blue", "option2": "50s"},
                        {"id": 2, "available": True, "price": "1100", "compare_at_price": "3000",
                         "option1": "Red", "option2": "50cm"}]}
    parsed = parser.parse_listing_page(json.dumps({"products": [raw]}),
                                      "https://example.com/collections/bikes?currency=USD")
    normalized = normalize(parsed, CYCLING, "example.com")
    result = query([source(normalized)], filters(size="50s"), now=NOW)
    assert result["total"] == 1 and result["cards"][0]["offer"]["variant_key"] == "1"
    result = query([source(normalized)], filters(size="50"), now=NOW)
    assert result["total"] == 1 and result["cards"][0]["offer"]["variant_key"] == "2"


def test_size_facets_use_one_stable_existing_label_per_match_key():
    from deal_common.offers import size_key

    labels = ['MEDIUM', 'MD', 'Medium', 'm', ' M ', 'M', 'S', 'SM', 'Small', 's',
              '50', '50cm', '50s', 'S/M', 'S/M/L', 'XS-M', 'XS/M', 'M18', 'm18']
    rows = [source([product('First', [offer(f'a-{i}', size=label) for i, label in enumerate(labels[:9])])]),
            {**source([product('Second', [offer(f'b-{i}', size=label)
                                         for i, label in enumerate(labels[9:])])]), 'name': 'Other'}]
    rows.append(source([product('Unknown', [offer('unknown', size='XL', stock='unknown')])]))
    rows.append(source([product('Stale', [offer('stale', size='XXL')])], NOW - timedelta(hours=25)))
    rows.append(source([product('Future', [offer('future', size='XXXL')])], NOW + timedelta(seconds=1)))
    result = query(rows, filters(), now=NOW)
    sizes = result['facets']['size']
    assert sizes == ['50', '50s', 'M', 'M18', 'S', 'S/M', 'S/M/L', 'XS-M', 'XS/M']
    assert len(sizes) == len({size_key(label) for label in sizes})
    assert set(sizes) <= set(labels)
    assert query(list(reversed(rows)), filters(), now=NOW)['facets']['size'] == sizes
    assert query(rows, filters(size='50'), now=NOW)['cards'][0]['offer']['size'] in {'50', '50cm'}
    assert query(rows, filters(size='50s'), now=NOW)['cards'][0]['offer']['size'] == '50s'
    assert query(rows, filters(size='S/M'), now=NOW)['cards'][0]['offer']['size'] == 'S/M'
    assert query(rows, filters(size='M18'), now=NOW)['cards'][0]['offer']['size'] in {'M18', 'm18'}


def test_size_facet_simplification_keeps_raw_offer_population_order_and_pagination():
    import json
    from copy import deepcopy

    aliases = ['M', 'MD', 'MEDIUM', 'Medium', 'm', ' M ']
    products = [product(f'P{i:02}', [offer(f'{i}-small', 100, 2000, 'S'),
                                   offer(f'{i}-medium', 500 + i, 2000, aliases[i % len(aliases)]),
                                   offer(f'{i}-unknown', 50, 2000, 'M', 'unknown')])
                for i in range(30)]
    products.append(product('Compound', [offer('compound', 100, 2000, 'S/M/L')]))
    rows = [source(products)]
    original = deepcopy(rows)
    expected = query(rows, filters(size='M'), now=NOW)
    assert expected['total'] == 30 and expected['pages'] == 2
    assert [card['name'] for card in expected['cards']] == [f'P{i:02}' for i in range(24)]
    page_two = query(rows, {**filters(size='M'), 'page': 2}, now=NOW)
    assert [card['name'] for card in page_two['cards']] == [f'P{i:02}' for i in range(24, 30)]
    expected_cards = expected['cards'] + page_two['cards']
    for i, card in enumerate(expected_cards):
        raw = original[0]['products'][i]['offers'][1]
        assert all(card['offer'][key] == value for key, value in raw.items())
        assert card['matching_variants'] == 1
    for alias in aliases:
        for page in (1, 2):
            actual = query(rows, {**filters(size=alias), 'page': page}, now=NOW)
            reference = query(rows, {**filters(size='M'), 'page': page}, now=NOW)
            assert json.dumps(actual['cards'], sort_keys=True) == json.dumps(reference['cards'], sort_keys=True)
            assert (actual['total'], actual['page'], actual['pages']) == (30, page, 2)
    assert rows == original


@pytest.mark.parametrize('catalog', [CYCLING, TOOLS])
def test_legacy_size_alias_selects_representative_and_links_without_changing_cards(tmp_path, catalog):
    from datetime import UTC
    from urllib.parse import parse_qs, urlsplit

    from bs4 import BeautifulSoup

    db = tmp_path / f'{catalog.slug}.db'
    config = RetailerConfig('Fixture', 'example.com', ['https://example.com/collection'])
    catalog = replace(catalog, sources=(config,))
    items = [product(f'P{i:02}', [offer(f'{i}-medium', 500 + i, 2000, 'MD' if i % 2 else 'M')])
             for i in range(27)]
    for item in items:
        item['category'] = catalog.categories[0]
    observed_at = datetime.now(UTC).isoformat()
    save_source(db, catalog.slug, config.name, observed_at, items, 'complete', {})
    client = TestClient(create_app(catalog, db))
    canonical = BeautifulSoup(client.get('/', params={'size': 'M'}).text, 'html.parser')
    for alias in ('MD', 'MEDIUM', 'Medium', ' m '):
        response = client.get('/', params={'size': alias})
        assert response.status_code == 200
        page = BeautifulSoup(response.text, 'html.parser')
        assert [option.get_text() for option in page.select('select[name="size"] option[selected]')] == ['M']
        assert [option.get_text() for option in page.select('select[name="size"] option')] == ['All ' + catalog.size_label.lower() + 's', 'M']
        assert page.select_one('.filter-note strong').get_text() == 'M'
        assert f'{catalog.size_label}: M' in page.select_one('.active-filters').get_text()
        assert [str(card) for card in page.select('article')] == [str(card) for card in canonical.select('article')]
        next_url = page.select_one('.pagination a')['href']
        assert parse_qs(urlsplit(next_url).query)['size'] == ['M']
        next_page = BeautifulSoup(client.get(next_url).text, 'html.parser')
        assert len(next_page.select('article')) == 3
        assert [option.get_text() for option in next_page.select('select[name="size"] option[selected]')] == ['M']
    unknown = 'Unlisted <size>'
    response = client.get('/', params={'size': unknown})
    page = BeautifulSoup(response.text, 'html.parser')
    assert [option.get_text() for option in page.select('select[name="size"] option[selected]')] == [unknown]
    assert page.select('article') == []
    assert 'No deals match' in page.get_text()
    assert '<size>' not in response.text


def test_size_representative_ignores_hidden_sources_and_unconfirmed_stock(tmp_path):
    from datetime import UTC

    from bs4 import BeautifulSoup

    config = RetailerConfig('Visible', 'example.com', ['https://example.com/collection'])
    catalog = replace(CYCLING, sources=(config,))
    db = tmp_path / 'visible-sizes.db'
    observed_at = datetime.now(UTC).isoformat()
    save_source(db, catalog.slug, config.name, observed_at, [
        product('Visible bike', [offer('visible', size='MD'),
                                 offer('unconfirmed', size='XL', stock='unknown')]),
    ], 'complete', {})
    save_source(db, catalog.slug, 'Unconfigured', observed_at, [
        product('Hidden bike', [offer('hidden-medium', size='M'), offer('hidden-small', size='XS')]),
    ], 'complete', {})
    original = db.read_bytes()
    client = TestClient(create_app(catalog, db))
    # A legacy saved-search URL must select the visible existing label, even
    # though an unconfigured source has the shorter equivalent representative.
    page = BeautifulSoup(client.get('/?size=Medium').text, 'html.parser')
    assert [option.get_text() for option in page.select('select[name="size"] option')] == ['All frame sizes', 'MD']
    assert [option.get_text() for option in page.select('select[name="size"] option[selected]')] == ['MD']
    assert [card.select_one('h3').get_text() for card in page.select('article')] == ['Visible bike']
    assert page.select_one('article a[href*="variant=visible"]') is not None
    unconfirmed = BeautifulSoup(client.get('/?size=XL').text, 'html.parser')
    assert unconfirmed.select('article') == []
    assert [option.get_text() for option in unconfirmed.select('select[name="size"] option[selected]')] == ['XL']
    assert db.read_bytes() == original


@pytest.mark.parametrize(('labels', 'expected'), [
    (['MD', 'Medium', 'MEDIUM'], ['MD']),
    ([' S / M ', 'S/M'], ['S/M']),
    (['50cm', '50 CM'], ['50cm']),
    (['M18', 'M12', 'm18'], ['M12', 'M18']),
])
def test_size_facet_representatives_are_existing_labels_not_invented_canonical_values(labels, expected):
    rows = [source([product(offers=[offer(str(i), size=label) for i, label in enumerate(labels)])])]
    assert query(rows, filters(), now=NOW)['facets']['size'] == expected
    rows[0]['products'][0]['offers'].reverse()
    assert query(rows, filters(), now=NOW)['facets']['size'] == expected
