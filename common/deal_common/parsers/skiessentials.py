"""Exact offers from Ski Essentials' public storefront collection feed."""
from __future__ import annotations

import json
import math
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.base import BaseParser
from deal_common.parsers.common import parse_price

ORIGIN = 'https://www.skiessentials.com'
FEED = 'https://services.mybcapps.com/bc-sf-filter/filter'
OPTION_NAMES = {
    'ski_size': 'ski size', 'board_size': 'board size', 'boot_size': 'boot size',
    'brake_size': 'brake size', 'binding_size': 'binding size', 'color': 'color',
}


def collection_identity(html: str, handle: str) -> str:
    """Read just the indexed collection identity; never evaluate merchant JS."""
    prefix = 'window.__reactRouterContext.streamController.enqueue('
    for script in BeautifulSoup(html, 'html.parser').select('script'):
        text = script.get_text().strip()
        if not text.startswith(prefix):
            continue
        try:
            encoded, _ = json.JSONDecoder().raw_decode(text[len(prefix):])
            table = json.loads(encoded)
        except (ValueError, TypeError):
            continue
        if not isinstance(table, list) or not table or len(table) > 200000:
            continue

        def deref(index, table=table):
            if type(index) is not int or not 0 <= index < len(table):
                raise ValueError('Invalid collection reference')
            return table[index]

        def field(index, name, deref=deref):
            row = deref(index)
            if not isinstance(row, dict):
                raise TypeError('Invalid collection object')
            matches = [v for k, v in row.items() if re.fullmatch(r'_\d+', k)
                       and deref(int(k[1:])) == name]
            if len(matches) != 1:
                raise ValueError('Missing or ambiguous collection field')
            return matches[0]

        try:
            loader = field(0, 'loaderData')
            route = field(loader, 'routes/collections.$handle')
            collection = field(route, 'collection')
            gid = deref(field(collection, 'id'))
            actual_handle = deref(field(collection, 'handle'))
        except (ValueError, TypeError):
            continue
        if (actual_handle != handle or not isinstance(gid, str)
                or not re.fullmatch(r'gid://shopify/Collection/\d+', gid)):
            raise ValueError('Collection identity mismatch')
        return gid.rsplit('/', 1)[1]
    raise ValueError('Missing collection identity')


def _money(value) -> float | None:
    # parse_price is permissive for display text; this feed must be a bare amount.
    if isinstance(value, bool) or not re.fullmatch(r'\d+(?:\.\d+)?', str(value)):
        return None
    amount = parse_price(str(value))
    return amount if amount is not None and math.isfinite(amount) and amount > 0 else None


def _online_prices(item: dict) -> dict:
    metadata = item.get('metafields')
    if not isinstance(metadata, list):
        raise TypeError('Missing SKU price metadata')
    selected = {}
    for row in metadata:
        if not isinstance(row, dict):
            raise TypeError('Malformed metadata')
        key = row.get('key')
        if row.get('namespace') == 'custom' and key in {'online_variant_prices', 'online_variant_lowest_price'}:
            if key in selected:
                raise ValueError('Ambiguous SKU price metadata')
            selected[key] = json.loads(row['value'])
    prices = selected.get('online_variant_prices')
    lowest = selected.get('online_variant_lowest_price')
    if not isinstance(prices, dict) or not isinstance(lowest, dict):
        raise TypeError('Missing SKU price/currency metadata')
    if lowest.get('currency_code') != 'USD':
        raise ValueError('Unconfirmed USD price')
    return prices


def _product(item: dict) -> Product | None:
    tags = item.get('tags', [])
    if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
        raise ValueError('Malformed product tags')
    # These entries are configurable packages, not standalone purchasable SKUs.
    if 'Bundle Product' in tags:
        return None
    handle, title = item.get('handle'), item.get('title')
    if not isinstance(handle, str) or not re.fullmatch(r'[a-zA-Z0-9-]+', handle) or not title:
        raise ValueError('Invalid product identity')
    url = f'{ORIGIN}/products/{handle}'
    prices = _online_prices(item)
    variants = item.get('variants')
    if not isinstance(variants, list) or any(not isinstance(v, dict) for v in variants):
        raise ValueError('Malformed variants')
    offers, seen_ids, seen_options = [], set(), set()
    for variant in variants:
        key, sku = str(variant.get('id', '')), variant.get('sku')
        if not key.isdigit() or key in seen_ids or not isinstance(sku, str) or not sku:
            raise ValueError('Invalid variant identity')
        seen_ids.add(key)
        raw_options = variant.get('merged_options')
        if not isinstance(raw_options, list) or any(not isinstance(o, str) for o in raw_options):
            raise ValueError('Malformed variant options')
        options = {}
        for option in raw_options:
            name, separator, value = option.partition(':')
            if not separator or not value or name in options:
                raise ValueError('Ambiguous variant options')
            options[name] = value
        if not options or not set(options) <= OPTION_NAMES.keys():
            continue  # Unverified option names cannot create exact purchase links.
        query = {OPTION_NAMES[k]: v.lower() for k, v in options.items()}
        identity = tuple(sorted(query.items()))
        if identity in seen_options:
            raise ValueError('Multiple variants share one destination')
        seen_options.add(identity)
        if variant.get('available') is False:
            continue
        price = _money(prices.get(sku))
        reference = _money(variant.get('compare_at_price_usd'))
        if price is None or reference is None or price >= reference:
            continue
        quantity = variant.get('inventory_quantity')
        confirmed = (variant.get('available') is True and type(quantity) is int and quantity > 0
                     and variant.get('inventory_management') == 'shopify'
                     and variant.get('inventory_policy') == 'deny')
        size = ' / '.join(v for k, v in options.items() if k.endswith('_size')) or None
        image = variant.get('image')
        if not isinstance(image, str) or urlsplit(image).scheme != 'https':
            images = item.get('images_info') or []
            image = images[0].get('src') if images and isinstance(images[0], dict) else None
        offers.append(VariantOffer(
            variant_key=key, url=url + '?' + urlencode(query), current_price=price,
            original_price=reference, size=size, options=' / '.join(options.values()),
            availability='in_stock' if confirmed else 'unknown', image_url=image,
        ))
    if not offers:
        return None
    best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
    return Product(
        name=title, url=url, current_price=best.current_price, original_price=best.original_price,
        image_url=best.image_url, brand=item.get('vendor'), product_type=item.get('product_type'),
        sizes=list(dict.fromkeys(o.size for o in offers if o.size and o.availability == 'in_stock')) or None,
        offers=offers, tags=tuple(tags),
    )


class SkiEssentialsParser(BaseParser):
    """Reconcile every page against a stable total and unique product IDs."""

    def __init__(self):
        self.scope = ''
        self.total: int | None = None
        self.seen: set[str] = set()
        self.next_url: str | None = None
        self.last_url = ''

    def _feed_url(self, page: int) -> str:
        return FEED + '?' + urlencode({
            'shop': 'skiess-test.myshopify.com', 'build_filter_tree': 'true',
            'check_cache': 'true', 'page': page, 'limit': 48, 'collection_scope': self.scope,
            'h_options': 'hide', 'variant_available': 'true',
        })

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        target = urlsplit(page_url)
        if target.scheme == 'https' and target.netloc == 'www.skiessentials.com':
            match = re.fullmatch(r'/collections/([a-zA-Z0-9-]+)', target.path)
            if not match or target.query or target.fragment:
                raise ValueError('Invalid collection URL')
            self.scope = collection_identity(html, match[1])
            self.total, self.seen = None, set()
            self.next_url = self._feed_url(1)
            self.last_url = page_url
            return []
        if page_url != self.next_url or not self.scope:
            raise ValueError('Unexpected collection feed page')
        data = json.loads(html)
        if not isinstance(data, dict):
            raise TypeError('Malformed collection feed')
        total, items = data.get('total_product'), data.get('products')
        if type(total) is not int or total < 0 or not isinstance(items, list):
            raise ValueError('Missing collection count or products')
        if self.total is not None and total != self.total:
            raise ValueError('Collection count changed during traversal')
        if len(items) != min(48, max(0, total - len(self.seen))):
            raise ValueError('Truncated collection page')
        ids = [str(item.get('id', '')) for item in items if isinstance(item, dict)]
        if (len(ids) != len(items) or any(not key.isdigit() for key in ids)
                or len(set(ids)) != len(ids) or set(ids) & self.seen):
            raise ValueError('Missing or repeated collection product IDs')
        products = [product for item in items if (product := _product(item)) is not None]
        self.total = total
        self.seen.update(ids)
        page = int(parse_qs(target.query)['page'][0])
        self.next_url = self._feed_url(page + 1) if len(self.seen) < total else None
        self.last_url = page_url
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        if current_url != self.last_url:
            raise ValueError('Pagination requested before page validation')
        return self.next_url
