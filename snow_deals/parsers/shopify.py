from __future__ import annotations

import json
import logging
import math
import re
from urllib.parse import urlparse

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)

def _products_json(body: str) -> list[dict]:
    """A malformed feed is a connection failure, not an empty collection."""
    data = json.loads(body)
    if not isinstance(data, dict) or not isinstance(data.get("products"), list):
        raise ValueError("Shopify feed is missing its products array")
    if any(not isinstance(item, dict) for item in data["products"]):
        raise ValueError("Shopify feed contains malformed products")
    return data["products"]


class ShopifyParser(BaseParser):
    """
    Parser for Shopify stores that expose /collections/{handle}/products.json.

    Works with Aspen Ski and Board and other Shopify-based retailers.
    Instead of scraping HTML, this parser uses the Shopify JSON API which
    provides structured price data including compare_at_price for discounts.
    """

    def _get_collection_handle(self, url: str) -> str | None:
        m = re.search(r"/collections/([^/?#]+)", urlparse(url).path)
        return m.group(1) if m else None

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        """Parse a Shopify products.json response (not HTML)."""
        items = _products_json(html)

        products: list[Product] = []
        origin = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"

        for item in items:
            if not item.get("handle") or not item.get("title"):
                continue
            variants = item.get("variants") or []
            # Skip products with no available variants — they're sold out.
            # Shopify variants have `available: bool`; if the field is missing
            # we assume available (some themes omit it).
            if variants and not any(v.get("available", True) for v in variants):
                continue

            # A card represents one actual offer, not unrelated variant prices/sizes.
            offers = []
            for candidate in variants:
                if not candidate.get("available", True):
                    continue
                try:
                    price = float(candidate.get("price") or 0)
                    original = float(candidate.get("compare_at_price") or 0)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(price) and math.isfinite(original) and 0 < price < original:
                    offers.append((price, original, candidate))
            if not offers:
                continue
            price, original_price, variant = min(offers, key=lambda offer: offer[0])
            sizes = []
            option_keys = [f"option{index + 1}" for index, option in enumerate(item.get("options") or [])
                           if any(word in str(option.get("name", "")).lower() for word in ("size", "length"))]
            for offer_price, offer_original, v in offers:
                if (offer_price, offer_original) != (price, original_price):
                    continue
                # Only use unnamed options when the value clearly looks like a size.
                for opt_key in option_keys or (() if item.get("options") else ("option1", "option2", "option3")):
                    val = v.get(opt_key)
                    if not option_keys and val and not re.fullmatch(r"(?:\d+(?:\.\d+)?\s*(?:cm|mm)?|[2-6]?X{0,3}[SML]|Small|Medium|Large)", str(val), re.I):
                        continue
                    if val and val != "Default Title" and val not in sizes:
                        sizes.append(val)

            # Extract first product image URL
            image_url = None
            images = item.get("images") or []
            if images:
                offer_image = next((image for image in images
                                    if variant.get("id") in (image.get("variant_ids") or [])), images[0])
                image_url = offer_image.get("src")
            elif item.get("image"):
                image_url = item["image"].get("src")

            products.append(Product(
                name=item.get("title", "Unknown"),
                url=f"{origin}/products/{item.get('handle', '')}",
                current_price=price,
                original_price=original_price,
                sizes=sizes or None,
                product_type=item.get("product_type") or None,
                image_url=image_url,
                brand=item.get("vendor") or None,
            ))

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        """Check if there are more pages of JSON results."""
        products = _products_json(html)
        m_limit = re.search(r"[?&]limit=(\d+)", current_url)
        limit = int(m_limit.group(1)) if m_limit else 250
        if len(products) < limit:
            return None

        # Increment page parameter
        m = re.search(r"[?&]page=(\d+)", current_url)
        current_page = int(m.group(1)) if m else 1
        next_page = current_page + 1

        # The orchestrator owns the page budget and reports truncation.
        base = current_url.split("?")[0]
        return f"{base}?limit={limit}&page={next_page}"

    def get_api_url(self, page_url: str, limit: int = 250) -> str | None:
        """Convert a collection URL to the Shopify JSON API URL."""
        handle = self._get_collection_handle(page_url)
        if not handle:
            return None
        parsed = urlparse(page_url)
        return f"{parsed.scheme}://{parsed.netloc}/collections/{handle}/products.json?limit={limit}&page=1"
