"""Grizzly's public JSON-LD: one purchasable SKU per product URL."""
import json
import math
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.base import BaseParser


def sku_destination(url: str, sku: str) -> bool:
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.netloc == "www.grizzly.com"
            and bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9-]+", sku))
            and parts.path.startswith("/products/")
            and parts.path.rstrip("/").split("/")[-1].casefold() == sku.casefold()
            and not parts.query and not parts.fragment)


def structured_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []
    recognized = False
    def visit(node):
        nonlocal recognized
        if isinstance(node, list):
            for child in node:
                visit(child)
        elif isinstance(node, dict):
            kind = node.get("@type")
            if kind == "Product":
                recognized = True
                products.append(node)
            elif kind == "ItemList":
                recognized = True
                visit(node.get("itemListElement", []))
            else:
                for key in ("@graph", "mainEntity", "item"):
                    if key in node:
                        visit(node[key])
    for script in soup.select('script[type="application/ld+json"]'):
        visit(json.loads(script.get_text()))
    if not recognized:
        raise ValueError("Missing Grizzly product data")
    return products


def text(value: str) -> str:
    # This retailer double-escapes some punctuation inside JSON string values.
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), value)


class GrizzlyParser(BaseParser):
    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        products = []
        for item in structured_products(html):
            offer = item.get("offers")
            if not isinstance(offer, dict) or offer.get("@type") != "Offer":
                continue
            reference = offer.get("priceSpecification")
            if not isinstance(reference, dict) or reference.get("priceType", "").split("/")[-1] != "StrikethroughPrice":
                continue
            if offer.get("priceCurrency") != "USD" or reference.get("priceCurrency") != "USD":
                raise ValueError("Grizzly currency is not USD")
            if offer.get("itemCondition", "").split("/")[-1] != "NewCondition":
                continue
            sku, url = str(item.get("sku") or ""), item.get("url") or ""
            if not sku_destination(url, sku) or offer.get("url") != url:
                continue
            try:
                price, original = float(offer["price"]), float(reference["price"])
            except (KeyError, TypeError, ValueError):
                continue
            if not all(map(math.isfinite, (price, original))) or not 0 < price < original:
                continue
            availability = offer.get("availability", "").split("/")[-1]
            if availability != "InStock":
                continue
            image = item.get("image") or {}
            image = image.get("url") if isinstance(image, dict) else image if isinstance(image, str) else None
            products.append(Product(
                name=text(item["name"]), url=url, current_price=price, original_price=original,
                product_type=text(item.get("category") or ""),
                brand=(item.get("brand") or {}).get("name"), image_url=image,
                offers=[VariantOffer(variant_key=sku, url=url, current_price=price,
                                     original_price=original, availability="in_stock", image_url=image)],
            ))
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        nav = soup.select_one("#search-pagination")
        if nav is None:
            raise ValueError("Missing Grizzly pagination evidence")
        summary = re.search(r"Page (\d+) of (\d+)", nav.get_text(" ", strip=True))
        if not summary:
            raise ValueError("Missing Grizzly page count")
        current, total = map(int, summary.groups())
        parts = urlsplit(current_url)
        query = dict(parse_qsl(parts.query))
        if current != int(query.get("cp", "1")) or not 1 <= current <= total:
            raise ValueError("Grizzly returned an unexpected page")
        if current == total:
            return None
        query["cp"] = str(current + 1)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
