from __future__ import annotations

import json
import logging
import math
import re
from urllib.parse import urlparse

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)

MAX_API_PAGES = 10


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
        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            log.warning("Response is not JSON, skipping: %s", page_url)
            return []

        products: list[Product] = []
        origin = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"

        for item in data.get("products", []):
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
                for opt_key in option_keys or ("option1", "option2", "option3"):
                    val = v.get(opt_key)
                    if val and val != "Default Title" and val not in sizes:
                        sizes.append(val)

            # Extract first product image URL
            image_url = None
            images = item.get("images") or []
            if images:
                image_url = images[0].get("src")
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
        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return None

        products = data.get("products", [])
        m_limit = re.search(r"[?&]limit=(\d+)", current_url)
        limit = int(m_limit.group(1)) if m_limit else 250
        if len(products) < limit:
            return None

        # Increment page parameter
        m = re.search(r"[?&]page=(\d+)", current_url)
        current_page = int(m.group(1)) if m else 1
        next_page = current_page + 1

        if next_page > MAX_API_PAGES:
            return None

        base = current_url.split("?")[0]
        return f"{base}?limit={limit}&page={next_page}"

    def get_api_url(self, page_url: str, limit: int = 250) -> str | None:
        """Convert a collection URL to the Shopify JSON API URL."""
        handle = self._get_collection_handle(page_url)
        if not handle:
            return None
        parsed = urlparse(page_url)
        return f"{parsed.scheme}://{parsed.netloc}/collections/{handle}/products.json?limit={limit}&page=1"
