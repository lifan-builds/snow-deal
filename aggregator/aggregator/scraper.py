"""Multi-store async scraping orchestrator."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import httpx

from aggregator.categorizer import categorize
from aggregator.config import STORES, StoreConfig
from aggregator.models import AggregatedDeal
from snow_deals.models import Product
from snow_deals.parsers.base import BaseParser
from snow_deals.parsers.bluezone import BlueZoneParser
from snow_deals.parsers.shopify import ShopifyParser

log = logging.getLogger(__name__)

# Per-domain semaphore to rate-limit concurrent requests
_semaphores: dict[str, asyncio.Semaphore] = {}
MAX_CONCURRENT_PER_DOMAIN = 2

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _get_semaphore(domain: str) -> asyncio.Semaphore:
    if domain not in _semaphores:
        _semaphores[domain] = asyncio.Semaphore(MAX_CONCURRENT_PER_DOMAIN)
    return _semaphores[domain]


def _get_parser(parser_type: str) -> BaseParser | None:
    """Return the appropriate parser instance for a given parser type."""
    if parser_type == "shopify":
        return ShopifyParser()
    elif parser_type == "bluezone":
        return BlueZoneParser()

    # Aggregator-specific BS4 parsers
    try:
        if parser_type == "alpineshopvt":
            from aggregator.parsers.alpineshopvt import AlpineShopVTParser
            return AlpineShopVTParser()
        elif parser_type == "thecircle":
            from aggregator.parsers.thecircle import TheCircleParser
            return TheCircleParser()
        elif parser_type == "coloradodiscount":
            from aggregator.parsers.coloradodiscount import ColoradoDiscountParser
            return ColoradoDiscountParser()
    except ImportError as e:
        log.error("Failed to import parser for type=%s: %s", parser_type, e)

    return None


def _products_to_deals(
    products: list[Product], store_name: str
) -> list[AggregatedDeal]:
    """Convert snow_deals Products to AggregatedDeals with categorization."""
    now = datetime.now()
    deals: list[AggregatedDeal] = []
    for p in products:
        deals.append(
            AggregatedDeal(
                id=None,
                store=store_name,
                name=p.name,
                url=p.url,
                current_price=p.current_price,
                original_price=p.original_price,
                discount_pct=p.discount_pct,
                category=categorize(p.name, p.url),
                image_url=p.image_url,
                scraped_at=now,
            )
        )
    return deals


async def scrape_store(
    store: StoreConfig,
    client: httpx.AsyncClient,
    *,
    delay: float = 1.0,
    max_pages: int = 10,
) -> list[AggregatedDeal]:
    """Scrape a single store using HTTP + parser and return AggregatedDeals."""
    sem = _get_semaphore(store.domain)

    parser = _get_parser(store.parser_type)
    if parser is None:
        log.warning("No parser for %s (type=%s), skipping", store.name, store.parser_type)
        return []

    products: list[Product] = []

    for url in store.scrape_urls:
        page = 0
        # For Shopify stores, convert to API URL
        if store.parser_type == "shopify" and isinstance(parser, ShopifyParser):
            current_url: str | None = parser.get_api_url(url)
            if not current_url:
                log.warning("Could not get API URL for %s", url)
                continue
        else:
            current_url = url

        while current_url and page < max_pages:
            page += 1
            async with sem:
                log.info("[%s] Fetching page %d: %s", store.name, page, current_url)
                try:
                    resp = await client.get(current_url)
                    resp.raise_for_status()
                except httpx.HTTPError as e:
                    log.error("[%s] HTTP error: %s", store.name, e)
                    break

            page_products = parser.parse_listing_page(resp.text, current_url)
            products.extend(page_products)

            if not page_products:
                break

            current_url = parser.get_next_page_url(resp.text, current_url)
            if current_url and page < max_pages:
                await asyncio.sleep(delay)

    log.info("[%s] Total products scraped: %d", store.name, len(products))
    return _products_to_deals(products, store.name)


async def scrape_store_browser(
    store: StoreConfig,
    *,
    delay: float = 2.0,
    max_pages: int = 3,
) -> list[AggregatedDeal]:
    """Scrape a single store using Playwright headless browser."""
    try:
        from aggregator.browser import scrape_with_browser
    except ImportError as e:
        log.error("[%s] Playwright not available: %s", store.name, e)
        return []

    products = await scrape_with_browser(
        urls=store.scrape_urls,
        store_name=store.name,
        store_type=store.parser_type,
        max_pages=max_pages,
        delay=delay,
    )
    log.info("[%s] Browser scraped %d products", store.name, len(products))
    return _products_to_deals(products, store.name)


async def scrape_all(
    *,
    stores: list[StoreConfig] | None = None,
    delay: float = 1.0,
    max_pages: int = 10,
) -> list[AggregatedDeal]:
    """Scrape all configured stores concurrently."""
    stores = stores or STORES

    http_stores = [s for s in stores if not s.use_browser]
    browser_stores = [s for s in stores if s.use_browser]

    all_deals: list[AggregatedDeal] = []

    # HTTP-based stores (Shopify JSON, BS4 HTML parsers)
    if http_stores:
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            tasks = [
                scrape_store(store, client, delay=delay, max_pages=max_pages)
                for store in http_stores
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for store, result in zip(http_stores, results):
            if isinstance(result, Exception):
                log.error("[%s] Scrape failed: %s", store.name, result)
            else:
                all_deals.extend(result)

    # Browser-based stores (Playwright)
    if browser_stores:
        browser_tasks = [
            scrape_store_browser(store, delay=delay, max_pages=min(max_pages, 3))
            for store in browser_stores
        ]
        results = await asyncio.gather(*browser_tasks, return_exceptions=True)

        for store, result in zip(browser_stores, results):
            if isinstance(result, Exception):
                log.error("[%s] Browser scrape failed: %s", store.name, result)
            else:
                all_deals.extend(result)

    return all_deals
