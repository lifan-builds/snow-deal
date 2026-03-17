from __future__ import annotations

import asyncio
import logging

import httpx

from deal.models import Product
from deal.parsers import get_parser

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_PAGES = 50  # safety cap


async def scrape(
    url: str,
    *,
    delay: float = 1.0,
    max_pages: int = MAX_PAGES,
) -> list[Product]:
    """
    Scrape all paginated product listings starting from *url*.

    Returns a flat list of Product objects across all pages.
    """
    from deal.parsers.shopify import ShopifyParser

    parser = get_parser(url)
    products: list[Product] = []

    # Shopify stores use a JSON API endpoint instead of the collection HTML URL
    if isinstance(parser, ShopifyParser):
        api_url = parser.get_api_url(url)
        if not api_url:
            raise ValueError(f"Could not determine Shopify collection handle from: {url}")
        current_url: str | None = api_url
    else:
        current_url = url

    page = 0

    async with httpx.AsyncClient(
        headers=DEFAULT_HEADERS,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        while current_url and page < max_pages:
            page += 1
            log.info("Fetching page %d: %s", page, current_url)

            resp = await client.get(current_url)
            resp.raise_for_status()
            html = resp.text

            page_products = parser.parse_listing_page(html, current_url)
            products.extend(page_products)
            log.info("Page %d: found %d products (total: %d)", page, len(page_products), len(products))

            if not page_products:
                break

            current_url = parser.get_next_page_url(html, current_url)

            if current_url and page < max_pages:
                await asyncio.sleep(delay)

    return products
