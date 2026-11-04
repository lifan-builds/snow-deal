"""Bounded HTTP pagination shared by category-specific scrape pipelines."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import re
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

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


async def fetch_listing(client: httpx.AsyncClient, url: str, delay: float,
                        *, follow_redirects: bool | None = None) -> httpx.Response:
    """Pace every request, including collection boundaries; retry temporary failures."""
    for attempt in range(4):
        await asyncio.sleep(max(delay, 0))
        try:
            options = {} if follow_redirects is None else {'follow_redirects': follow_redirects}
            response = await client.get(url, **options)
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 3:
                response.raise_for_status()
                return response
            retry_after = response.headers.get("Retry-After", "")
            try:
                seconds = float(retry_after)
            except ValueError:
                try:
                    seconds = (parsedate_to_datetime(retry_after) - datetime.now(UTC)).total_seconds()
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
                         max_pages: int = 10, outcome: dict | None = None,
                         include_product: Callable[[Product], bool] | None = None,
                         max_product_pages: int = 500) -> list[Product]:
    """Read bounded collections, preserving coverage and failure evidence."""
    if outcome is None:
        outcome = {"errors": 0, "pages": 0}
    products: list[Product] = []
    details_seen: set[str] = set()

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
            except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
                collection['status'] = 'currency_check_failed'
                if isinstance(exc, httpx.HTTPStatusError):
                    collection['http_status'] = exc.response.status_code
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
                parser.validate_listing_response(resp.text, current_url, dict(resp.headers))
                page_products = parser.parse_listing_page(resp.text, current_url)
                next_url = parser.get_next_page_url(resp.text, current_url)
                if parser.requires_product_pages:
                    resolved = []
                    for product in page_products:
                        if product.url in details_seen or (include_product and not include_product(product)):
                            continue
                        target = urlsplit(product.url)
                        if (target.scheme != 'https' or target.hostname != store.domain
                                or target.username or target.password or target.port not in (None, 443)):
                            raise ValueError('Unsafe product detail destination')
                        if len(details_seen) >= max_product_pages:
                            raise ValueError('Product detail page budget exhausted')
                        details_seen.add(product.url)
                        async with semaphore:
                            detail = await fetch_listing(client, product.url, delay)
                        if urlsplit(str(detail.url)).hostname != store.domain:
                            raise ValueError('Product detail redirected off source')
                        outcome['product_pages'] = outcome.get('product_pages', 0) + 1
                        evidence_url = parser.get_product_evidence_url(detail.text, product.url)
                        if evidence_url:
                            evidence_target = urlsplit(evidence_url)
                            if (evidence_target.scheme != 'https' or evidence_target.hostname != store.domain
                                    or evidence_target.username or evidence_target.password
                                    or evidence_target.port not in (None, 443)):
                                raise ValueError('Unsafe product evidence destination')
                            async with semaphore:
                                evidence = await fetch_listing(client, evidence_url, delay, follow_redirects=False)
                            if urlsplit(str(evidence.url)).hostname != store.domain:
                                raise ValueError('Product evidence redirected off source')
                            outcome['evidence_requests'] = outcome.get('evidence_requests', 0) + 1
                            resolved.extend(parser.parse_product_evidence(detail.text, product.url, evidence.text))
                        else:
                            resolved.extend(parser.parse_product_page(detail.text, product.url))
                    page_products = resolved
                products.extend(page_products)
                collection["products"] += len(page_products)
                current_url = next_url
            except httpx.HTTPError as exc:
                outcome['errors'] += 1
                collection['status'] = 'product_http_error'
                if isinstance(exc, httpx.HTTPStatusError):
                    collection['http_status'] = exc.response.status_code
                break
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
