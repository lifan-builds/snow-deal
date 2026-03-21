from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser

log = logging.getLogger(__name__)


def _parse_price(text: str) -> float | None:
    """Extract a numeric price from text like 'C$485.99' or '$485.99'."""
    match = re.search(r"(?:C?\$)?([\d,]+\.?\d*)", text.strip())
    if match:
        return float(match.group(1).replace(",", ""))
    return None


class TheCircleParser(BaseParser):
    """Parser for thecirclewhistler.com (Lightspeed) product listing pages."""

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, "lxml")
        products: list[Product] = []

        for card in soup.select(".product-card"):
            product = self._parse_card(card, page_url)
            if product:
                products.append(product)

        log.info("Parsed %d products from %s", len(products), page_url)
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")

        next_link = soup.select_one('a.next, a[rel="next"]')
        if not next_link:
            # Look for next-page link in any pagination container
            for pagination in soup.select(".pagination, .pager, nav[aria-label]"):
                for link in pagination.find_all("a"):
                    text = link.get_text(strip=True).lower()
                    if text in ("next", "›", "»", ">"):
                        next_link = link
                        break
                if next_link:
                    break

        if next_link and next_link.get("href"):
            return urljoin(current_url, next_link["href"])
        return None

    def _parse_card(self, card: Tag, page_url: str) -> Product | None:
        # Product name
        name_el = card.select_one(".product-name")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name:
            return None

        # Product URL: prefer .product-name href, fall back to .product-link
        href = name_el.get("href")
        if not href:
            link_el = card.select_one(".product-link")
            if link_el:
                href = link_el.get("href")
        url = urljoin(page_url, href) if href else page_url

        # Prices
        current_price: float | None = None
        original_price: float | None = None

        orig_el = card.select_one(".original-price")
        sale_el = card.select_one(".sale-price")

        if orig_el and sale_el:
            original_price = _parse_price(orig_el.get_text(strip=True))
            current_price = _parse_price(sale_el.get_text(strip=True))
        elif sale_el:
            current_price = _parse_price(sale_el.get_text(strip=True))
        elif orig_el:
            current_price = _parse_price(orig_el.get_text(strip=True))
        else:
            # Try price-container as a whole
            price_container = card.select_one(".price-container")
            if price_container:
                current_price = _parse_price(price_container.get_text(strip=True))

        if current_price is None:
            return None

        # Image
        image_url = None
        img = card.select_one(".product-image")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                image_url = urljoin(page_url, str(src))

        return Product(
            name=name,
            url=url,
            current_price=current_price,
            original_price=original_price,
            image_url=image_url,
        )
