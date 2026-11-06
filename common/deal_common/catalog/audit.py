"""Independent product-endpoint checks against selected listing offers.

This checks merchant-reported facts, not checkout completion or former street prices.
No browser session, cart contents, cookies, credentials or raw response is persisted.
"""
import hashlib
import random
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx

from deal_common.catalog.refresh import safe_url
from deal_common.http import DEFAULT_HEADERS, fetch_listing
from deal_common.parsers.availability import shipping_notice
from deal_common.parsers.beaver import detail_data as beaver_data
from deal_common.parsers.bikecloset import API as BIKECLOSET_API
from deal_common.parsers.bikecloset import decode_offer as bikecloset_offer
from deal_common.parsers.bikecloset import manufacturer as bikecloset_manufacturer
from deal_common.parsers.bikecloset import money as bikecloset_money
from deal_common.parsers.bikecloset import new_condition as bikecloset_new
from deal_common.parsers.bikecloset import offer_destination as bikecloset_destination
from deal_common.parsers.bolton import detail_data as bolton_data
from deal_common.parsers.bolton import offer_destination as bolton_destination
from deal_common.parsers.grizzly import sku_destination, structured_products
from deal_common.parsers.grizzly import text as decoded_text
from deal_common.parsers.racycles import detail_data as racycles_data
from deal_common.parsers.rockler import delivery_data, stock_url
from deal_common.parsers.rockler import detail_data as rockler_data
from deal_common.parsers.rockler import offer_destination as rockler_destination
from deal_common.parsers.shopify import is_contender_generated_variant
from deal_common.parsers.taylor import detail_data as taylor_data
from deal_common.parsers.taylor import offer_destination as taylor_destination


def select_sample(cards: list[dict], seed: int = 20261102) -> list[dict]:
    # Input is already selected/ranked; don't give products with many variants more weight.
    top = cards[:10]
    rest = sorted(cards[10:], key=lambda c: (c["store"], c["url"]))
    return top + random.Random(seed).sample(rest, min(20, len(rest)))


def validate_product(card: dict, raw: dict, currency: str | None) -> dict:
    offer = card["offer"]
    variants = raw.get("variants")
    if not isinstance(variants, list):
        return {"status": "inconclusive", "reason": "Malformed product response"}
    matches = [v for v in variants if isinstance(v, dict) and str(v.get("id")) == offer["variant_key"]]
    if len(matches) != 1:
        return {"status": "inconclusive", "reason": "Variant absent or ambiguous; endpoint may truncate variants"}
    actual = matches[0]
    def cents_equal(value, expected):
        try:
            return not isinstance(value, bool) and Decimal(str(value)) / 100 == Decimal(str(expected))
        except (InvalidOperation, TypeError, ValueError):
            return False
    expected_options = offer.get("options", "")
    option_definitions = raw.get("options") or []
    price_positions = {i for i, definition in enumerate(option_definitions)
                       if isinstance(definition, dict) and re.search(
                           r"\b(?:msrp|retail|price)\b", str(definition.get("name", "")), re.IGNORECASE)}
    # A declared MSRP metadata option is not a purchasable size/color choice.
    # Preserve its raw value in evidence, but compare actual variant dimensions.
    raw_options = actual.get("options", [])
    actual_options = " / ".join(str(v) for i, v in enumerate(raw_options)
                                if i not in price_positions and v != "Default Title")
    notice = shipping_notice(raw, actual, offer["url"])
    checks = {
        "identity": str(raw.get("title", "")).strip() == card["name"].strip(),
        "currency": currency == card.get("currency", "USD"),
        "price": cents_equal(actual.get("price"), offer["current_price"]),
        "reference": cents_equal(actual.get("compare_at_price"), offer["original_price"]),
        "options": actual_options == expected_options,
        "stock": actual.get("available") is True and not notice,
    }
    if is_contender_generated_variant(actual, offer["url"]):
        checks["ordinary_variant"] = False
    return {"status": "match" if all(checks.values()) else "mismatch", "checks": checks,
            "merchant": {"title": raw.get("title"), "variant": str(actual["id"]), "sku": actual.get("sku"),
                         "price_minor": actual.get("price"), "reference_minor": actual.get("compare_at_price"),
                         "currency": currency, "options": actual_options, "raw_options": raw_options,
                         "option_definitions": option_definitions, "available": actual.get("available"),
                         "shipping_notice": notice}}


async def audit_sample(cards: list[dict], allowed_domains: dict[str, str], *, delay: float = 5.0,
                       transport=None) -> list[dict]:
    results = []
    sampled_at = datetime.now(UTC)
    expired = False

    def within_window(now):
        nonlocal expired
        expired = expired or not 0 <= (now - sampled_at).total_seconds() <= 15 * 60
        return not expired

    def record(row):
        finished_at = datetime.now(UTC)
        timely = within_window(finished_at)
        row.update(sampled_at=sampled_at.isoformat(), checked_at=finished_at.isoformat(),
                   within_audit_window=timely)
        if not timely:
            row.update(status='inconclusive', reason='Outside the 15-minute audit observation window')
        results.append(row)
    currencies = {}
    blocked = set()
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=20, transport=transport,
                                 follow_redirects=False) as client:
        async def fetch(url):
            if not within_window(datetime.now(UTC)):
                raise TimeoutError('Audit observation window expired')
            return await fetch_listing(client, url, delay)

        for card in cards:
            offer = card["offer"]
            parts = urlsplit(offer["url"])
            domain = allowed_domains.get(card["store"])
            row = {"name": card["name"], "store": card["store"], "offer": offer,
                   "check_started_at": datetime.now(UTC).isoformat()}
            if not within_window(datetime.now(UTC)):
                record({**row, 'status': 'inconclusive', 'reason': 'Audit observation window expired'})
                continue
            sku_product = sku_destination(offer["url"], offer["variant_key"])
            taylor_product = taylor_destination(offer['url'], offer['variant_key'])
            rockler_product = rockler_destination(offer['url'], offer['variant_key'])
            bolton_product = bolton_destination(offer['url'], offer['variant_key'])
            bikecloset_product = bikecloset_destination(offer['url'], offer['variant_key'])
            if (not domain or not safe_url(offer["url"], domain)
                    or (not (taylor_product or rockler_product or bikecloset_product or bolton_product) and ("/products/" not in parts.path
                        or (not sku_product and parse_qs(parts.query).get("variant") != [offer["variant_key"]])))):
                record({**row, "status": "inconclusive", "reason": "Unsupported or unsafe product destination"})
                continue
            origin = f"{parts.scheme}://{parts.netloc}"
            prefix = parts.path.split("/products/", 1)[0]
            currency_url = origin + prefix + "/cart.js?" + urlencode({"currency": card.get("currency", "USD")})
            endpoint = urlunsplit((parts.scheme, parts.netloc, parts.path + ".js",
                                  urlencode({"currency": card.get("currency", "USD")}), ""))
            row["evidence_url"] = offer["url"] if sku_product or taylor_product or rockler_product or bolton_product else endpoint
            if origin in blocked:
                record({**row, "status": "inconclusive", "reason": "Host blocked or rate-limited earlier in this audit"})
                continue
            try:
                if bolton_product:
                    response = await fetch(offer['url'])
                    row['response_sha256'] = hashlib.sha256(response.content).hexdigest()
                    row.update(validate_bolton_product(card, bolton_data(response.text, offer['url'])))
                    record(row)
                    continue
                if bikecloset_product:
                    parent_id, variant_id = offer['variant_key'].split('|')[0].split(':')
                    row['evidence_url'] = BIKECLOSET_API + '/' + variant_id
                    response = await fetch(row['evidence_url'])
                    parent_url = BIKECLOSET_API + '/' + parent_id
                    parent = await fetch(parent_url)
                    row.update(response_sha256=hashlib.sha256(response.content).hexdigest(),
                               parent_evidence_url=parent_url,
                               parent_response_sha256=hashlib.sha256(parent.content).hexdigest())
                    row.update(validate_bikecloset_product(card, parent.json(), response.json()))
                    record(row)
                    continue
                if rockler_product:
                    response = await fetch(offer['url'])
                    product = rockler_data(response.text, offer['url'])
                    evidence_url = stock_url(product)
                    stock = await fetch(evidence_url)
                    row.update(response_sha256=hashlib.sha256(response.content).hexdigest(),
                               stock_evidence_url=evidence_url,
                               stock_response_sha256=hashlib.sha256(stock.content).hexdigest())
                    row.update(validate_rockler_product(card, product, delivery_data(stock.json())))
                    record(row)
                    continue
                if taylor_product:
                    response = await fetch(offer['url'])
                    row['response_sha256'] = hashlib.sha256(response.content).hexdigest()
                    row.update(validate_taylor_product(card, taylor_data(response.text, offer['url'])))
                    record(row)
                    continue
                if sku_product:
                    response = await fetch(offer["url"])
                    row["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                    row.update(validate_sku_product(card, structured_products(response.text)))
                    record(row)
                    continue
                if origin not in currencies:
                    response = await fetch(currency_url)
                    # Only the currency is retained from this new anonymous session.
                    currencies[origin] = response.json().get("currency")
                if currencies[origin] != card.get("currency", "USD"):
                    record({**row, "status": "inconclusive", "reason": "Presentment currency not confirmed"})
                    continue
                response = await fetch(endpoint)
                raw = response.json()
                if not isinstance(raw, dict):
                    raise TypeError("Malformed product")
                row["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                row.update(validate_product(card, raw, currencies[origin]))
                if parts.hostname in {'beavertools.com', 'racycles.com'}:
                    page = await fetch(offer['url'])
                    if parts.hostname == 'beavertools.com':
                        detail = validate_beaver_product(card, beaver_data(page.text, offer['url']))
                    else:
                        detail = validate_racycles_product(card, racycles_data(page.text, offer['url'], raw))
                    row.update(product_evidence_url=offer['url'],
                               product_response_sha256=hashlib.sha256(page.content).hexdigest())
                    if 'checks' not in row:
                        row['checks'] = {'product_endpoint': False}
                    row['checks'].update({'purchase_' + key: value for key, value in detail['checks'].items()})
                    if row['status'] != 'inconclusive':
                        row['status'] = 'match' if all(row['checks'].values()) else 'mismatch'
                    row['purchase_panel'] = detail['merchant']
            except TimeoutError:
                row.update(status='inconclusive', reason='Audit observation window expired')
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in {403, 429}:
                    blocked.add(origin)
                row.update(status="inconclusive", reason=f"HTTP {status}")
            except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError):
                row.update(status="inconclusive", reason="Response could not be verified")
            record(row)
    return results


def validate_bikecloset_product(card, parent, variant):
    expected = card['offer']
    actual = bikecloset_offer(parent, variant)
    checks = {
        'identity': unescape(parent['name']) == card['name'],
        'currency': variant['prices']['currency_code'] == card.get('currency', 'USD'),
        'price': bikecloset_money(variant['prices'], 'price') == expected['current_price'],
        'reference': bikecloset_money(variant['prices'], 'regular_price') == expected['original_price'],
        'condition': bikecloset_new(parent),
        'stock': actual is not None and actual.availability == 'in_stock',
        'destination': actual is not None and actual.url == expected['url'] and actual.variant_key == expected['variant_key'],
        'options': actual is not None and actual.options == expected.get('options') and actual.size == expected.get('size'),
        'shipping_note': actual is not None and actual.availability_note == expected.get('availability_note', ''),
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {'parent_id': parent['id'], 'variant_id': variant['id'], 'sku': variant.get('sku'),
                         'brand': bikecloset_manufacturer(parent),
                         'price': bikecloset_money(variant['prices'], 'price'),
                         'reference': bikecloset_money(variant['prices'], 'regular_price'),
                         'currency': variant['prices']['currency_code'], 'is_in_stock': variant['is_in_stock'],
                         'is_on_backorder': variant['is_on_backorder']}}


def validate_racycles_product(card: dict, product: dict) -> dict:
    expected = card['offer']
    actual = product['variants'].get(expected['variant_key'])
    if actual is None:
        return {'checks': {'identity': False}, 'merchant': {'reason': 'Selected variant absent'}}
    checks = {
        'identity': product['name'] == card['name'] and product['selected_key'] == expected['variant_key'],
        'destination': urlsplit(actual['url']).path == urlsplit(expected['url']).path,
        'currency': product['currency'] == card.get('currency', 'USD'),
        'price': actual['price'] == expected['current_price'],
        'reference': actual['reference'] == expected['original_price'],
        'options': actual['options'] == expected.get('options', ''),
        'size': not expected.get('size') or actual['size'] == expected['size'],
        'stock': actual['in_stock'],
        'shipping_note': actual['shipping_note'] == expected.get('availability_note', ''),
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {key: actual[key] for key in ('sku', 'price', 'reference', 'options', 'size',
                        'qty', 'virtual_warehouse', 'shipping_note')}}


def validate_beaver_product(card: dict, product: dict) -> dict:
    expected = card['offer']
    checks = {
        'identity': product['name'] == card['name'] and product['variant_key'] == expected['variant_key'],
        'destination': urlsplit(product['url']).path == urlsplit(expected['url']).path,
        'currency': product['currency'] == card.get('currency', 'USD'),
        'price': product['price'] == expected['current_price'],
        'reference': product['reference'] == expected['original_price'],
        'options': product['options'] == expected.get('options', '') and not expected.get('size'),
        'stock': product['in_stock'],
        'shipping_note': product['shipping_note'] == expected.get('availability_note', ''),
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {key: product[key] for key in ('sku', 'product_id', 'variant_key', 'price',
                        'reference', 'currency', 'stock_label', 'shipping_note')}}


def validate_bolton_product(card: dict, product: dict) -> dict:
    expected = card['offer']
    checks = {
        'identity': product['name'] == card['name'] and product['variant_key'] == expected['variant_key'],
        'destination': product['url'] == expected['url'] and bolton_destination(expected['url'], product['variant_key']),
        'currency': product['currency'] == card.get('currency', 'USD'),
        'price': product['price'] == expected['current_price'],
        'reference': product['reference'] == expected['original_price'],
        'options': product['options'] == expected.get('options') and not expected.get('size'),
        'condition': product['condition'] == 'NewCondition',
        'stock': product['in_stock'],
        'shipping_note': product['shipping_note'] == expected.get('availability_note', ''),
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {key: product[key] for key in ('sku', 'variant_key', 'price', 'reference',
                        'currency', 'condition', 'in_stock', 'shipping_note')}}


def validate_rockler_product(card: dict, product: dict, delivery: dict) -> dict:
    expected = card['offer']
    key = f"{product['sku']}|{product['uid']}|{urlsplit(product['url']).path}"
    checks = {
        'identity': product['name'] == card['name'] and key == expected['variant_key'],
        'destination': product['url'] == expected['url'] and rockler_destination(expected['url'], key),
        'currency': card.get('currency', 'USD') == 'USD',  # decoder requires explicit USD
        'price': product['price'] == expected['current_price'],
        'reference': product['reference'] == expected['original_price'],
        'options': expected.get('options') == f"SKU {product['sku']}",
        'condition': product['condition'] == 'https://schema.org/NewCondition',
        'stock': delivery['available'] and delivery['availability'] == 'in_stock',
        'shipping_note': expected.get('availability_note', '') == delivery['note'],
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {'sku': product['sku'], 'product_id': product['uid'],
                         'price': product['price'], 'reference': product['reference'], 'currency': 'USD',
                         'schema_availability': product['schema_availability'], 'delivery': delivery}}


def validate_taylor_product(card: dict, product: dict) -> dict:
    expected = card['offer']
    sku, _, query = expected['variant_key'].partition('|')
    actual = product['skus'].get(sku)
    if actual is None:
        return {'status': 'inconclusive', 'reason': 'SKU absent from Taylor product page'}
    def equal(value, target):
        try:
            return not isinstance(value, bool) and Decimal(str(value)) == Decimal(str(target))
        except (InvalidOperation, ValueError, TypeError):
            return False
    try:
        quantity = Decimal(str(actual.get('qty')))
        has_stock = quantity.is_finite() and quantity > 0
    except (InvalidOperation, ValueError, TypeError):
        has_stock = False
    checks = {
        'identity': product['name'] == card['name'],
        'destination': actual['query'] == query and taylor_destination(expected['url'], expected['variant_key']),
        'currency': True,  # detail_data requires the explicit US-only price container.
        'price': equal(actual.get('price'), expected['current_price']),
        'reference': equal(actual.get('regular_price'), expected['original_price']),
        'options': actual['options'] == expected.get('options'),
        'stock': actual.get('available') is True and actual.get('ib') is False and has_stock,
        'condition': actual.get('level_name') == 'Regular',
    }
    return {'status': 'match' if all(checks.values()) else 'mismatch', 'checks': checks,
            'merchant': {'sku': actual['vendor_sku'], 'selector_sku': sku, 'selection': actual['selection'],
                         'price': actual.get('price'), 'reference': actual.get('regular_price'),
                         'stock': actual.get('qty'), 'options': actual['options'], 'currency': 'USD'}}


def validate_sku_product(card: dict, products: list[dict]) -> dict:
    """Compare a Grizzly listing with its separate, exact-SKU product page."""
    expected = card["offer"]
    matches = [p for p in products if p.get("sku") == expected["variant_key"] and p.get("url") == expected["url"]]
    if len(matches) != 1:
        return {"status": "inconclusive", "reason": "SKU absent or ambiguous on product page"}
    product = matches[0]
    actual = product.get("offers") or {}
    reference = actual.get("priceSpecification") or {}
    def equal(value, target):
        try:
            return not isinstance(value, bool) and Decimal(str(value)) == Decimal(str(target))
        except (InvalidOperation, ValueError, TypeError):
            return False
    checks = {
        "identity": decoded_text(product.get("name", "")) == card["name"],
        "destination": actual.get("url") == expected["url"],
        "currency": actual.get("priceCurrency") == reference.get("priceCurrency") == "USD",
        "price": equal(actual.get("price"), expected["current_price"]),
        "reference": (equal(reference.get("price"), expected["original_price"])
                      and reference.get("priceType", "").split("/")[-1] == "StrikethroughPrice"),
        "stock": actual.get("availability", "").split("/")[-1] == "InStock",
        "condition": actual.get("itemCondition", "").split("/")[-1] == "NewCondition",
        "options": not expected.get("options") and not expected.get("size"),
    }
    return {"status": "match" if all(checks.values()) else "mismatch", "checks": checks,
            "merchant": {"sku": product.get("sku"), "price": actual.get("price"),
                         "reference": reference.get("price"), "currency": actual.get("priceCurrency"),
                         "availability": actual.get("availability"), "condition": actual.get("itemCondition")}}


def audit_summary(results):
    counts = {status: sum(row["status"] == status for row in results) for status in ("match", "mismatch", "inconclusive")}
    return {"sample_size": len(results), **counts,
            "verified_match_percent": round(100 * counts["match"] / len(results), 2) if results else None,
            "scope": "Anonymous merchant product endpoint and currency; not checkout or historical-reference validation",
            "results": results}
