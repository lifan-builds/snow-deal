"""Independent product-endpoint checks against selected listing offers.

This checks merchant-reported facts, not checkout completion or former street prices.
No browser session, cart contents, cookies, credentials or raw response is persisted.
"""
import asyncio
import hashlib
import random
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx

from deal_common.catalog.refresh import safe_url
from deal_common.http import DEFAULT_HEADERS
from deal_common.parsers.grizzly import sku_destination, structured_products
from deal_common.parsers.grizzly import text as decoded_text


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
    checks = {
        "identity": str(raw.get("title", "")).strip() == card["name"].strip(),
        "currency": currency == card.get("currency", "USD"),
        "price": cents_equal(actual.get("price"), offer["current_price"]),
        "reference": cents_equal(actual.get("compare_at_price"), offer["original_price"]),
        "options": actual_options == expected_options,
        "stock": actual.get("available") is True,
    }
    return {"status": "match" if all(checks.values()) else "mismatch", "checks": checks,
            "merchant": {"title": raw.get("title"), "variant": str(actual["id"]), "sku": actual.get("sku"),
                         "price_minor": actual.get("price"), "reference_minor": actual.get("compare_at_price"),
                         "currency": currency, "options": actual_options, "raw_options": raw_options,
                         "option_definitions": option_definitions, "available": actual.get("available")}}


async def audit_sample(cards: list[dict], allowed_domains: dict[str, str], *, delay: float = 1.5,
                       transport=None) -> list[dict]:
    results = []
    currencies = {}
    blocked = set()
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=20, transport=transport,
                                 follow_redirects=False) as client:
        for card in cards:
            offer = card["offer"]
            parts = urlsplit(offer["url"])
            domain = allowed_domains.get(card["store"])
            row = {"name": card["name"], "store": card["store"], "offer": offer,
                   "checked_at": datetime.now(UTC).isoformat()}
            sku_product = sku_destination(offer["url"], offer["variant_key"])
            if (not domain or not safe_url(offer["url"], domain) or "/products/" not in parts.path
                    or (not sku_product and parse_qs(parts.query).get("variant") != [offer["variant_key"]])):
                results.append({**row, "status": "inconclusive", "reason": "Unsupported or unsafe product destination"})
                continue
            origin = f"{parts.scheme}://{parts.netloc}"
            prefix = parts.path.split("/products/", 1)[0]
            currency_url = origin + prefix + "/cart.js?" + urlencode({"currency": card.get("currency", "USD")})
            endpoint = urlunsplit((parts.scheme, parts.netloc, parts.path + ".js",
                                  urlencode({"currency": card.get("currency", "USD")}), ""))
            row["evidence_url"] = offer["url"] if sku_product else endpoint
            if origin in blocked:
                results.append({**row, "status": "inconclusive", "reason": "Host blocked or rate-limited earlier in this audit"})
                continue
            try:
                if sku_product:
                    await asyncio.sleep(delay)
                    response = await client.get(offer["url"])
                    response.raise_for_status()
                    row["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                    row.update(validate_sku_product(card, structured_products(response.text)))
                    results.append(row)
                    continue
                if origin not in currencies:
                    await asyncio.sleep(delay)
                    response = await client.get(currency_url)
                    response.raise_for_status()
                    # Only the currency is retained from this new anonymous session.
                    currencies[origin] = response.json().get("currency")
                if currencies[origin] != card.get("currency", "USD"):
                    results.append({**row, "status": "inconclusive", "reason": "Presentment currency not confirmed"})
                    continue
                await asyncio.sleep(delay)
                response = await client.get(endpoint)
                response.raise_for_status()
                raw = response.json()
                if not isinstance(raw, dict):
                    raise TypeError("Malformed product")
                row["response_sha256"] = hashlib.sha256(response.content).hexdigest()
                row.update(validate_product(card, raw, currencies[origin]))
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in {403, 429}:
                    blocked.add(origin)
                row.update(status="inconclusive", reason=f"HTTP {status}")
            except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                row.update(status="inconclusive", reason="Response could not be verified")
            results.append(row)
    return results


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
