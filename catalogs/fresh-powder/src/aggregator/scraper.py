"""Multi-store async scraping orchestrator."""

from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, replace
import logging
import math
import hashlib
import json
import re
import random
from email.utils import parsedate_to_datetime
from datetime import timezone
from datetime import datetime
from urllib.parse import urlparse

import httpx

from aggregator.categorizer import categorize, exclusion_reason
from aggregator.reviews import _extract_brand, _normalize_brand
from aggregator.config import STORES, StoreConfig
from aggregator.models import AggregatedDeal
from aggregator.sizes import extract_lengths as _extract_lengths
from deal_common.parsers.common import clean_product_name
from deal_common.models import Product
from deal_common.http import DEFAULT_HEADERS, fetch_products, fetch_listing
from deal_common.parsers.base import BaseParser

log = logging.getLogger(__name__)

# Per-domain semaphore to rate-limit concurrent requests
_semaphores: dict[str, asyncio.Semaphore] = {}
MAX_CONCURRENT_PER_DOMAIN = 2



def _get_semaphore(domain: str) -> asyncio.Semaphore:
    if domain not in _semaphores:
        _semaphores[domain] = asyncio.Semaphore(MAX_CONCURRENT_PER_DOMAIN)
    return _semaphores[domain]


# Registry mapping parser_type -> (module_path, class_name)
# Browser-only stores (evo, backcountry, thehouse, etc.) are handled by browser.py
# and don't need entries here.
_PARSER_REGISTRY: dict[str, tuple[str, str]] = {
    "shopify":          ("deal_common.parsers.shopify", "ShopifyParser"),
    "skiessentials":    ("deal_common.parsers.skiessentials", "SkiEssentialsParser"),
    "bluezone":         ("snow_deals.parsers.bluezone", "BlueZoneParser"),
    "alpineshopvt":     ("aggregator.parsers.alpineshopvt", "AlpineShopVTParser"),
    "thecircle":        ("aggregator.parsers.thecircle", "TheCircleParser"),
    "coloradodiscount": ("aggregator.parsers.coloradodiscount", "ColoradoDiscountParser"),
    "sacredride":       ("aggregator.parsers.sacredride", "SacredRideParser"),
}


def _get_parser(parser_type: str) -> BaseParser | None:
    """Return the appropriate parser instance for a given parser type."""
    entry = _PARSER_REGISTRY.get(parser_type)
    if entry is None:
        return None
    module_path, class_name = entry
    try:
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()
    except (ImportError, AttributeError) as e:
        log.error("Failed to load parser %s.%s: %s", module_path, class_name, e)
        return None


_RETAIL_PATTERN = re.compile(r',?\s*Retail(?:\s+Price)?:\s*\$[\d,.]+', re.IGNORECASE)
_PRICE_PATTERN = re.compile(r'\$[\d,.]+')
_COLOR_JUNK = re.compile(
    r'\b(Multicolor|Default Title|One Size|One Color)\b,?\s*', re.IGNORECASE
)
# Common color names to strip from sizes
_COLORS = re.compile(
    r'\b(Red|Blue|Green|Black|White|Grey|Gray|Navy|Orange|Yellow|Purple|Pink|Brown|'
    r'Teal|Coral|Sage Green|Black/Black|White/White|Solid \w+)\b/?\.?\s*,?\s*',
    re.IGNORECASE
)


def _clean_sizes(sizes_str: str | None) -> str | None:
    """Clean sizes string by removing prices, colors, and junk values."""
    if not sizes_str:
        return None
    s = _RETAIL_PATTERN.sub('', sizes_str)
    # If the remaining string is mostly prices (e.g. "$0.98, $1.98, ..."), discard it
    parts = [p.strip() for p in s.split(',') if p.strip()]
    non_price_parts = [p for p in parts if not _PRICE_PATTERN.fullmatch(p.strip())
                       and p.upper() not in {'NA', 'N/A', 'N.A.', 'NONE', 'UNKNOWN'}]
    if not non_price_parts:
        return None
    s = ', '.join(non_price_parts)
    s = _COLOR_JUNK.sub('', s)
    s = _COLORS.sub('', s)
    s = re.sub(r',\s*,', ',', s).strip(' ,')
    # Truncate overly long sizes
    if len(s) > 120:
        s = s[:117] + '...'
    return s if s else None


@dataclass(frozen=True)
class StoreScrapeSummary:
    """Per-store scrape quality counters."""

    store: str
    deals: int
    missing_category: int
    missing_image: int
    missing_sizes: int
    missing_lengths: int
    length_eligible: int
    variant_offers: int
    deals_with_variants: int
    confirmed_size_deals: int


@dataclass(frozen=True)
class ScrapeReport:
    """Aggregate scrape quality report for a refresh run."""

    configured_stores: int
    stores_with_deals: int
    total_deals: int
    zero_count_stores: list[str]
    store_summaries: list[StoreScrapeSummary]
    missing_category: int
    missing_image: int
    missing_sizes: int
    missing_lengths: int
    length_eligible: int
    variant_offers: int
    deals_with_variants: int
    confirmed_size_deals: int


def _is_kids_product(name: str) -> bool:
    """Return True if the product name indicates kids/junior gear."""
    return exclusion_reason(name) == 'children'


def _products_to_deals(
    products: list[Product], store_name: str
) -> list[AggregatedDeal]:
    """Convert shared Products to AggregatedDeals with categorization.

    Filters out kids/junior products.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    deals: list[AggregatedDeal] = []
    for p in products:
        if p.offers:
            offers = [o for o in p.offers if o.current_price >= 1 and 0 < o.discount_pct < 95]
            if not offers:
                continue
            best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
            p = replace(p, current_price=best.current_price, original_price=best.original_price,
                        image_url=best.image_url, offers=offers,
                        sizes=list(dict.fromkeys(o.size for o in offers if o.size and
                              (o.current_price, o.original_price) == (best.current_price, best.original_price))))
        name = clean_product_name(p.name, p.url)
        if not name:
            continue
        source_description = f"{name} {p.product_type or ''} {p.brand or ''}"
        if exclusion_reason(source_description, p.url):
            continue
        if (not math.isfinite(p.current_price) or p.original_price is None
                or not math.isfinite(p.original_price)
                or urlparse(p.url).scheme not in {"https", "http"}
                or not urlparse(p.url).netloc):
            continue
        if p.current_price < 1 or p.discount_pct <= 0 or p.discount_pct >= 95:
            continue
        category = categorize(name, p.url, p.product_type or "", brand=p.brand or "")
        raw_sizes = ", ".join(p.sizes) if p.sizes else None
        if category in {"skis", "snowboards"} and raw_sizes:
            raw_sizes = re.sub(r"(?<![\d.])\b(1\d{2}|2[01]\d|220)\b(?!\s*cm|[\d.])", r"\1cm", raw_sizes)

        length_min, length_max = _extract_lengths(raw_sizes) if category in {"skis", "snowboards"} else (None, None)
        sizes_str = _clean_sizes(raw_sizes)
        deals.append(
            AggregatedDeal(
                id=None,
                store=store_name,
                name=name,
                url=p.url,
                current_price=p.current_price,
                original_price=p.original_price,
                discount_pct=p.discount_pct,
                category=category,
                sizes=sizes_str,
                length_min=length_min,
                length_max=length_max,
                scraped_at=now,
                image_url=p.image_url,
                product_type=p.product_type,
                offers=p.offers,
                brand=_normalize_brand(p.brand) if p.brand else (_extract_brand(name) or None),
            )
        )
    return deals


def build_scrape_report(
    deals: list[AggregatedDeal],
    stores: list[StoreConfig] | None = None,
) -> ScrapeReport:
    """Build per-store count and data-completeness metrics for observability."""
    stores = stores or STORES
    configured_names = [s.name for s in stores]
    deals_by_store: dict[str, list[AggregatedDeal]] = {name: [] for name in configured_names}
    for deal in deals:
        deals_by_store.setdefault(deal.store, []).append(deal)

    summaries: list[StoreScrapeSummary] = []
    for store_name in configured_names:
        store_deals = deals_by_store.get(store_name, [])
        summaries.append(
            StoreScrapeSummary(
                store=store_name,
                deals=len(store_deals),
                missing_category=sum(1 for d in store_deals if not d.category),
                missing_image=sum(1 for d in store_deals if not d.image_url),
                missing_sizes=sum(1 for d in store_deals if not d.sizes),
                missing_lengths=sum(1 for d in store_deals if d.category in {"skis", "snowboards"} and d.length_min is None),
                length_eligible=sum(d.category in {"skis", "snowboards"} for d in store_deals),
                variant_offers=sum(len(d.offers) for d in store_deals),
                deals_with_variants=sum(bool(d.offers) for d in store_deals),
                confirmed_size_deals=sum(any(o.size and o.availability == 'in_stock' for o in d.offers)
                                         for d in store_deals),
            )
        )

    counts = Counter(d.store for d in deals)
    zero_count_stores = [name for name in configured_names if counts.get(name, 0) == 0]
    return ScrapeReport(
        configured_stores=len(configured_names),
        stores_with_deals=sum(1 for name in configured_names if counts.get(name, 0) > 0),
        total_deals=len(deals),
        zero_count_stores=zero_count_stores,
        store_summaries=summaries,
        missing_category=sum(1 for d in deals if not d.category),
        missing_image=sum(1 for d in deals if not d.image_url),
        missing_sizes=sum(1 for d in deals if not d.sizes),
        missing_lengths=sum(1 for d in deals if d.category in {"skis", "snowboards"} and d.length_min is None),
        length_eligible=sum(d.category in {"skis", "snowboards"} for d in deals),
        variant_offers=sum(len(d.offers) for d in deals),
        deals_with_variants=sum(bool(d.offers) for d in deals),
        confirmed_size_deals=sum(any(o.size and o.availability == 'in_stock' for o in d.offers)
                                 for d in deals),
    )


async def scrape_store(
    store: StoreConfig,
    client: httpx.AsyncClient,
    *,
    delay: float = 1.0,
    max_pages: int = 10,
    outcomes: dict | None = None,
) -> list[AggregatedDeal]:
    """Scrape a single store using HTTP + parser and return AggregatedDeals."""
    sem = _get_semaphore(store.domain)
    outcome = outcomes.setdefault(store.name, {"errors": 0, "pages": 0}) if outcomes is not None else {"errors": 0, "pages": 0}

    parser = _get_parser(store.parser_type)
    if parser is None:
        outcome["errors"] += 1
        log.warning("No parser for %s (type=%s), skipping", store.name, store.parser_type)
        return []

    products = await fetch_products(store, parser, client, semaphore=sem, delay=delay,
                                    max_pages=max_pages, outcome=outcome)
    deals = list({d.url: d for d in _products_to_deals(products, store.name)}.values())
    for deal in deals:
        deal.currency = store.currency
    return deals


async def scrape_store_browser(
    store: StoreConfig,
    *,
    delay: float = 2.0,
    max_pages: int = 25,
    outcomes: dict | None = None,
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
        outcome=outcomes.setdefault(store.name, {"errors": 0, "pages": 0}) if outcomes is not None else None,
    )
    log.info("[%s] Browser scraped %d products", store.name, len(products))
    return list({d.url: d for d in _products_to_deals(products, store.name)}.values())


async def scrape_all(
    *,
    stores: list[StoreConfig] | None = None,
    delay: float = 1.0,
    max_pages: int = 10,
    outcomes: dict | None = None,
) -> list[AggregatedDeal]:
    """Scrape all configured stores concurrently."""
    stores = stores or STORES
    _semaphores.clear()

    http_stores = [s for s in stores if not s.use_browser]
    browser_stores = [s for s in stores if s.use_browser]

    all_deals: list[AggregatedDeal] = []
    http_limit = asyncio.Semaphore(3)
    # Shopify stores share infrastructure. Avoid concurrent feed bursts across
    # domains even though their individual per-domain limits allow them.
    shopify_limit = asyncio.Semaphore(1)
    browser_limit = asyncio.Semaphore(3)

    async def bounded_http(store, client):
        async with http_limit:
            if store.parser_type == "shopify":
                async with shopify_limit:
                    return await scrape_store(store, client, delay=delay, max_pages=max_pages, outcomes=outcomes)
            return await scrape_store(store, client, delay=delay, max_pages=max_pages, outcomes=outcomes)

    async def bounded_browser(store):
        async with browser_limit:
            return await scrape_store_browser(store, delay=delay, max_pages=max_pages, outcomes=outcomes)


    # HTTP-based stores (Shopify JSON, BS4 HTML parsers)
    if http_stores:
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            follow_redirects=True,
            timeout=30.0,
        ) as client:
            tasks = [
                bounded_http(store, client)
                for store in http_stores
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for store, result in zip(http_stores, results):
                if isinstance(result, Exception):
                    log.error("[%s] Scrape failed: %s", store.name, result)
                    if outcomes is not None:
                        outcomes.setdefault(store.name, {"errors": 0, "pages": 0})["errors"] += 1
                    result = []
                if not result:
                    log.warning("[%s] Returned zero deals; retrying once", store.name)
                    try:
                        result = await scrape_store(store, client, delay=delay, max_pages=max_pages, outcomes=outcomes)
                    except Exception as exc:
                        log.error("[%s] Retry failed: %s", store.name, exc)
                        result = []
                log.info("[%s] Completed: %d deals after filtering", store.name, len(result))
                all_deals.extend(result)

    # Browser-based stores (Playwright)
    if browser_stores:
        browser_tasks = [
            bounded_browser(store)
            for store in browser_stores
        ]
        results = await asyncio.gather(*browser_tasks, return_exceptions=True)

        for store, result in zip(browser_stores, results):
            if isinstance(result, Exception):
                log.error("[%s] Browser scrape failed: %s", store.name, result)
                if outcomes is not None:
                    outcomes.setdefault(store.name, {"errors": 0, "pages": 0})["errors"] += 1
            else:
                log.info("[%s] Completed: %d deals after filtering", store.name, len(result))
                all_deals.extend(result)

    all_deals = list({d.url: d for d in all_deals}.values())
    report = build_scrape_report(all_deals, stores)
    if report.zero_count_stores:
        log.warning("Zero-count stores: %s", ", ".join(report.zero_count_stores))
    log.info(
        "Scrape quality: deals=%d stores=%d/%d missing_category=%d missing_image=%d missing_sizes=%d missing_lengths=%d",
        report.total_deals,
        report.stores_with_deals,
        report.configured_stores,
        report.missing_category,
        report.missing_image,
        report.missing_sizes,
        report.missing_lengths,
    )
    return all_deals


def protect_partial_snapshots(deals: list[AggregatedDeal], previous: dict[str, int], outcomes: dict) -> tuple[list[AggregatedDeal], list[str]]:
    """Don't replace a recent substantial snapshot with an unexplained collapse.

    Retained rows keep their original timestamps and expire through the normal
    72-hour freshness filter. The caller supplies only recent baselines, so a
    genuine sustained sell-through does not leave a source quarantined forever.
    """
    counts = Counter(d.store for d in deals)
    withheld = [store for store, count in previous.items()
                if count >= 20 and counts[store] < count * 0.3]
    for store in withheld:
        result = outcomes.setdefault(store, {"errors": 0, "pages": 0})
        result["count_drop"] = {"previous": previous[store], "current": counts[store]}
        result["errors"] += 1
    return [d for d in deals if d.store not in withheld], withheld
