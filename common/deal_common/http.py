"""Bounded HTTP pagination shared by category-specific scrape pipelines."""

from __future__ import annotations

import asyncio
import logging
import hashlib
import json
import re
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from deal_common.config import RetailerConfig
from deal_common.models import Product
from deal_common.parsers.base import BaseParser

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


async def fetch_listing(client: httpx.AsyncClient, url: str, delay: float) -> httpx.Response:
    """Pace every request, including collection boundaries; retry temporary failures."""
    for attempt in range(4):
        await asyncio.sleep(max(delay, 0))
        try:
            response = await client.get(url)
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 3:
                response.raise_for_status()
                return response
            retry_after = response.headers.get("Retry-After", "")
            try:
                seconds = float(retry_after)
            except ValueError:
                try:
                    seconds = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
                except (ValueError, TypeError):
                    seconds = 2 ** (attempt + 2) + random.random()
            # Do not retry sooner than a retailer requests when the wait exceeds our budget.
            if seconds > 60:
                response.raise_for_status()
            await asyncio.sleep(max(0, seconds))
        except httpx.TransportError:
            if attempt == 3:
                raise
            await asyncio.sleep(2 ** (attempt + 2))
    raise RuntimeError("Unreachable retry state")


async def fetch_products(store: RetailerConfig, parser: BaseParser, client: httpx.AsyncClient,
                         *, semaphore: asyncio.Semaphore, delay: float = 1.0,
                         max_pages: int = 10, outcome: dict | None = None) -> list[Product]:
    """Read bounded collections, preserving coverage and failure evidence."""
    if outcome is None:
        outcome = {"errors": 0, "pages": 0}
    products: list[Product] = []

    for url in store.scrape_urls:
        page = 0
        seen_pages: set[str] = set()
        collection = {"url": url, "pages": 0, "products": 0, "status": "complete"}
        outcome.setdefault("collections", []).append(collection)
        if store.parser_type == "shopify" and store.verify_shopify_currency:
            try:
                storefront = await fetch_listing(client, url, delay)
                match = re.search(r'Shopify\.currency\s*=\s*(\{[^;]+?\})\s*;', storefront.text)
                observed = json.loads(match.group(1)).get('active') if match else None
                collection['observed_currency'] = observed
                if observed != store.currency:
                    collection['status'] = 'currency_mismatch' if observed else 'currency_unknown'
                    outcome['errors'] += 1
                    continue
            except (httpx.HTTPError, ValueError, TypeError, AttributeError):
                collection['status'] = 'currency_check_failed'
                outcome['errors'] += 1
                continue
        # For Shopify stores, convert to API URL
        if store.parser_type == "shopify" and hasattr(parser, "get_api_url"):
            current_url: str | None = parser.get_api_url(
                url,
                limit=store.shopify_products_limit,
            )
            if not current_url:
                outcome["errors"] += 1
                collection["status"] = "invalid_url"
                log.warning("Could not get API URL for %s", url)
                continue
        else:
            current_url = url

        while current_url and page < max_pages:
            page += 1
            async with semaphore:
                log.info("[%s] Fetching page %d: %s", store.name, page, current_url)
                try:
                    resp = await fetch_listing(client, current_url, delay)
                    outcome["pages"] += 1
                    collection["pages"] += 1
                except httpx.HTTPError as e:
                    outcome["errors"] += 1
                    collection["status"] = "http_error"
                    if isinstance(e, httpx.HTTPStatusError):
                        collection["http_status"] = e.response.status_code
                    log.error("[%s] HTTP error: %s", store.name, e)
                    break

            fingerprint = hashlib.sha256(resp.content).hexdigest()
            if fingerprint in seen_pages:
                outcome["errors"] += 1
                collection["status"] = "repeated_page"
                break
            seen_pages.add(fingerprint)
            try:
                page_products = parser.parse_listing_page(resp.text, current_url)
                products.extend(page_products)
                collection["products"] += len(page_products)
                current_url = parser.get_next_page_url(resp.text, current_url)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                outcome["errors"] += 1
                collection["status"] = "parse_error"
                log.error("[%s] Invalid listing at %s: %s", store.name, current_url, type(exc).__name__)
                break
            if current_url and page >= max_pages:
                outcome["errors"] += 1
                collection["status"] = "page_limit"
            if current_url and page < max_pages:
                await asyncio.sleep(delay)

    return products
