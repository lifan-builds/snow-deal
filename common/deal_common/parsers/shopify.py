from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from urllib.parse import parse_qsl, urlencode, urlparse

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.availability import shipping_notice
from deal_common.parsers.base import BaseParser

log = logging.getLogger(__name__)


def is_contender_generated_variant(variant: dict, url: str) -> bool:
    """Exclude observed generated choices without aliasing their prices or stock."""
    if urlparse(url).hostname not in {"contenderbicycles.com", "www.contenderbicycles.com"}:
        return False
    values = [variant.get(key) for key in ("title", "option1", "option2", "option3")]
    if isinstance(variant.get("options"), list):
        values.extend(variant["options"])
    return any(isinstance(value, str) and re.search(r"(?<!\w)#MWS Options [0-9]+(?!\w)", value)
               for value in values)


def pricing_notice(item: dict, url: str) -> str:
    """Retain the observed merchant caveat without changing price or stock."""
    if urlparse(url).hostname not in {"contenderbicycles.com", "www.contenderbicycles.com"}:
        return ""
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split(",")
    if isinstance(tags, list) and any(isinstance(tag, str) and tag.strip() == "contact-for-current-price"
                                      for tag in tags):
        return "Retailer asks you to contact them for current pricing."
    return ""


def _products_json(body: str) -> list[dict]:
    """A malformed feed is a connection failure, not an empty collection."""
    data = json.loads(body)
    if not isinstance(data, dict) or not isinstance(data.get("products"), list):
        raise ValueError("Shopify feed is missing its products array")
    if any(not isinstance(item, dict) for item in data["products"]):
        raise ValueError("Shopify feed contains malformed products")
    return data["products"]


def product_type_from_item(item: dict) -> str:
    """Retain the retailer's readable taxonomy when its type is an internal code."""
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",")]
    taxonomy = {}
    for tag in tags:
        key, separator, value = str(tag).partition(":")
        if separator and key in {"BreadcrumbClass", "BreadcrumbSubBMC"}:
            taxonomy[key] = value.strip()
    if taxonomy.get("BreadcrumbClass"):
        result = " | ".join(taxonomy[key] for key in ("BreadcrumbClass", "BreadcrumbSubBMC") if taxonomy.get(key))
    else:
        explicit_tags = {str(tag).strip() for tag in tags if str(tag).startswith('Gear: ')}
        if len(explicit_tags) == 1:
            result = explicit_tags.pop().removeprefix('Gear: ')
        elif 'Skis:' in tags or 'Skis' in tags:
            result = 'Skis'
        else:
            result = str(item.get("product_type") or "")
    if any(str(tag).strip().lower() in {'kids', 'junior', 'youth', 'boys', 'girls', 'gender/age:kids'} for tag in tags):
        result += ' | Kids'
    return result


class ShopifyParser(BaseParser):
    """
    Parser for Shopify stores that expose /collections/{handle}/products.json.

    Works with Aspen Ski and Board and other Shopify-based retailers.
    Instead of scraping HTML, this parser uses the Shopify JSON API which
    provides structured price data including compare_at_price for discounts.
    """

    def __init__(self, *, size_option_names: tuple[str, ...] = (), size_value_pattern: str = ""):
        # Catalogs may distinguish frame size from wheel size. Empty preserves
        # the snow parser's existing size/length discovery contract.
        self.size_option_names = {name.casefold() for name in size_option_names}
        self.size_value_pattern = re.compile(size_value_pattern, re.I) if size_value_pattern else None

    def _get_collection_handle(self, url: str) -> str | None:
        m = re.search(r"/collections/([^/?#]+)", urlparse(url).path)
        return m.group(1) if m else None

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        """Parse a Shopify products.json response (not HTML)."""
        items = _products_json(html)

        products: list[Product] = []
        origin = f"{urlparse(page_url).scheme}://{urlparse(page_url).netloc}"
        # Shopify Markets can localize both prices and product destinations.
        prefix = urlparse(page_url).path.split('/collections/', 1)[0] if '/collections/' in urlparse(page_url).path else ''
        currency = dict(parse_qsl(urlparse(page_url).query)).get('currency')
        currency_query = '?' + urlencode({'currency': currency}) if currency else ''

        for item in items:
            if not item.get("handle") or not item.get("title"):
                continue
            variants = item.get("variants") or []
            product_url = f"{origin}{prefix}/products/{item['handle']}{currency_query}"
            images = item.get("images") or []
            default_image = images[0].get("src") if images else (item.get("image") or {}).get("src")
            option_keys = [f"option{index + 1}" for index, option in enumerate(item.get("options") or [])
                           if isinstance(option, dict) and (
                               str(option.get("name", "")).strip().casefold() in self.size_option_names
                               if self.size_option_names else any(
                                   word in str(option.get("name", "")).lower() for word in ("size", "length")))]
            price_keys = {f"option{index + 1}" for index, option in enumerate(item.get("options") or [])
                          if isinstance(option, dict) and re.search(r"\b(msrp|retail|price)\b", str(option.get('name', '')), re.I)}
            offers = []
            for index, candidate in enumerate(variants):
                if (not isinstance(candidate, dict) or candidate.get("available") is False
                        or is_contender_generated_variant(candidate, product_url)):
                    continue
                try:
                    price = float(candidate.get("price") or 0)
                    original = float(candidate.get("compare_at_price") or 0)
                except (TypeError, ValueError):
                    continue
                if not (math.isfinite(price) and math.isfinite(original) and 0 < price < original):
                    continue
                sizes = []
                for key in option_keys or (() if item.get("options") or self.size_option_names else ("option1", "option2", "option3")):
                    value = str(candidate.get(key) or '').strip()
                    if self.size_value_pattern and not self.size_value_pattern.fullmatch(value):
                        continue
                    if not option_keys and not re.fullmatch(r"(?:\d+(?:\.\d+)?\s*(?:cm|mm)?|[2-6]?X{0,3}[SML]|Small|Medium|Large)", value, re.I):
                        continue
                    if value and value != 'Default Title':
                        sizes.append(value)
                variant_id = candidate.get('id')
                query = dict(parse_qsl(urlparse(product_url).query))
                if variant_id is not None:
                    query['variant'] = str(variant_id)
                variant_url = product_url.split('?')[0] + ('?' + urlencode(query) if query else '')
                image = next((img.get('src') for img in images if variant_id is not None
                              and variant_id in (img.get('variant_ids') or [])), default_image)
                notice = shipping_notice(item, candidate, product_url)
                offers.append(VariantOffer(
                    variant_key=str(variant_id) if variant_id is not None else "options-" + hashlib.sha256(json.dumps([candidate.get(k) for k in ("sku", "option1", "option2", "option3")]).encode()).hexdigest()[:20],
                    url=variant_url, current_price=price, original_price=original,
                    size=' / '.join(sizes) or None,
                    options=' / '.join(str(candidate[k]) for k in ('option1', 'option2', 'option3')
                                       if k not in price_keys and candidate.get(k) and candidate[k] != 'Default Title'),
                    availability='in_stock' if candidate.get('available') is True and not notice else 'unknown',
                    image_url=image,
                    availability_note=notice,
                    price_note=pricing_notice(item, product_url),
                ))
            if not offers:
                continue
            best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
            price, original_price, image_url = best.current_price, best.original_price, best.image_url
            sizes = list(dict.fromkeys(o.size for o in offers if o.size and
                                      (o.current_price, o.original_price) == (price, original_price)))

            products.append(Product(
                name=item.get("title", "Unknown"),
                url=product_url,
                current_price=price,
                original_price=original_price,
                sizes=sizes or None,
                product_type=product_type_from_item(item) or None,
                image_url=image_url,
                brand=item.get("vendor") or None,
                offers=offers,
                tags=tuple(tag.strip() for tag in (
                    item.get("tags", "").split(",") if isinstance(item.get("tags"), str)
                    else item.get("tags") or []) if isinstance(tag, str)),
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
        query = dict(parse_qsl(urlparse(current_url).query))
        query.update(limit=limit, page=next_page)
        return f"{base}?{urlencode(query)}"

    def get_api_url(self, page_url: str, limit: int = 250) -> str | None:
        """Convert a collection URL to the Shopify JSON API URL."""
        handle = self._get_collection_handle(page_url)
        if not handle:
            return None
        parsed = urlparse(page_url)
        prefix = parsed.path.split('/collections/', 1)[0]
        query = {'limit': limit, 'page': 1}
        currency = dict(parse_qsl(parsed.query)).get('currency')
        if currency:
            query['currency'] = currency
        return f"{parsed.scheme}://{parsed.netloc}{prefix}/collections/{handle}/products.json?{urlencode(query)}"
