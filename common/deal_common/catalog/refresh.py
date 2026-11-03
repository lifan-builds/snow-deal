"""Bounded source refreshes keep previous complete data on a partial response."""
import asyncio
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx

from deal_common.catalog.definition import Catalog
from deal_common.catalog.storage import save_source
from deal_common.http import DEFAULT_HEADERS, fetch_products
from deal_common.offers import discount
from deal_common.parsers.grizzly import GrizzlyParser, sku_destination
from deal_common.parsers.shopify import ShopifyParser
from deal_common.parsers.taylor import TaylorParser
from deal_common.parsers.taylor import offer_destination as taylor_destination


def safe_url(value: str | None, domain: str | None = None) -> bool:
    if not value:
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and parsed.port in (None, 443)
                and (domain is None or parsed.hostname.removeprefix("www.") == domain.removeprefix("www.")))
    except ValueError:
        return False


def normalize(products, catalog: Catalog, domain: str, *, parser_type: str = "shopify") -> list[dict]:
    result = {}
    brands = dict(catalog.brand_aliases)
    for product in products:
        classification = catalog.classify(product)
        if not classification or classification.category not in catalog.categories or not safe_url(product.url, domain):
            continue
        offers = []
        for offer in product.offers:
            if parser_type == 'grizzly':
                destination_matches = sku_destination(offer.url, offer.variant_key)
            elif parser_type == 'taylor':
                destination_matches = taylor_destination(offer.url, offer.variant_key)
            else:
                destination_matches = parse_qs(urlsplit(offer.url).query).get('variant') == [offer.variant_key]
            if (offer.availability not in {"in_stock", "unknown"}
                    or discount(offer.current_price, offer.original_price) <= 0
                    or not safe_url(offer.url, domain)
                    or urlsplit(offer.url).path != urlsplit(product.url).path
                    or not destination_matches):
                continue
            data = asdict(offer)
            data["image_url"] = offer.image_url if safe_url(offer.image_url) else None
            offers.append(data)
        if not offers:
            continue
        original_brand = (product.brand or "Unspecified").strip()
        # Some storefronts put fulfillment messages in Shopify's vendor field.
        # They establish neither a manufacturer nor variant stock evidence.
        if re.fullmatch(r"in stock|out of stock|esd[:：].*", original_brand, re.IGNORECASE):
            original_brand = "Unspecified"
        row = {"name": product.name, "url": product.url,
               "brand": brands.get(original_brand.casefold(), original_brand),
               "source_category": product.product_type,
               **asdict(classification), "offers": offers}
        result[product.url] = row
    return list(result.values())


async def refresh(catalog: Catalog, path: Path, *, max_pages: int = 30,
                  delay: float = 1.5, transport=None) -> list[dict]:
    reports = []
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=30, follow_redirects=True,
                                 transport=transport) as client:
        for source in catalog.sources:
            outcome = {"errors": 0, "pages": 0}
            observed_at = datetime.now(UTC).isoformat()
            if source.currency != "USD":
                raise ValueError("These catalogs accept USD sources only")
            if source.parser_type not in {"shopify", "grizzly", "taylor"}:
                raise ValueError("Unsupported catalog parser")
            if source.parser_type == 'taylor':
                parser = TaylorParser()
            elif source.parser_type == 'grizzly':
                parser = GrizzlyParser()
            else:
                parser = ShopifyParser(size_option_names=catalog.size_option_names,
                                       size_value_pattern=catalog.size_value_pattern)
            products = await fetch_products(source, parser, client,
                                            semaphore=asyncio.Semaphore(1), delay=delay,
                                            max_pages=max_pages, outcome=outcome,
                                            include_product=lambda product: catalog.classify(product) is not None)
            normalized = normalize(products, catalog, source.domain, parser_type=source.parser_type)
            status = "complete" if outcome["errors"] == 0 and outcome.get("collections") else "incomplete"
            outcome.update(parsed_products=len(products), accepted_products=len(normalized))
            save_source(path, catalog.slug, source.name, observed_at, normalized, status, outcome)
            reports.append({"source": source.name, "status": status, **outcome})
    return reports
