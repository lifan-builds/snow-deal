"""Rockler category discovery, exact simple SKUs and public delivery evidence."""
import json
import math
import re
from html import unescape
from urllib.parse import parse_qs, urlencode, urlsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.base import BaseParser
from deal_common.parsers.common import parse_price

ORIGIN = 'https://www.rockler.com'
CATEGORY_API = 'https://rn129l.a.searchspring.io/api/search/category.json'
SALE_FILTERS = ('Clearance', 'Flash Sale', 'Sale', 'Free Gift')


def listing_url(page: int = 1) -> str:
    params = [('siteId', 'rn129l'), ('resultsFormat', 'json'), ('disableInlineBanners', 'true'),
              ('bgfilter.ss_category', 'Power Tools'), ('page', str(page))]
    params += [('filter.ss_morewaystoshop', tag) for tag in SALE_FILTERS]
    return CATEGORY_API + '?' + urlencode(params)


def product_url(value: str) -> str:
    if value.startswith('/'):
        value = ORIGIN + value
    parts = urlsplit(value)
    if (parts.scheme != 'https' or parts.netloc != 'www.rockler.com' or parts.query or parts.fragment
            or not re.fullmatch(r'/[a-z0-9][a-z0-9-]*', parts.path)):
        raise ValueError('Invalid Rockler product destination')
    return value


def offer_destination(url: str, key: str) -> bool:
    try:
        product_url(url)
        sku, uid, path = key.split('|')
        return sku.isdigit() and uid.isdigit() and path == urlsplit(url).path
    except (ValueError, AttributeError):
        return False


def text(value) -> str:
    return BeautifulSoup(str(value or ''), 'html.parser').get_text(' ', strip=True)


def amount(value) -> float:
    if isinstance(value, bool) or not re.fullmatch(r'\d+(?:\.\d+)?', str(value)):
        raise ValueError('Malformed Rockler amount')
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Invalid Rockler amount')
    return result


def detail_data(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select_one('link[rel="canonical"]')
    if not canonical or product_url(canonical.get('href', '')) != product_url(url):
        raise ValueError('Rockler canonical identity mismatch')
    configs = []
    for script in soup.select('script[type="text/x-magento-init"]'):
        payload = json.loads(script.get_text())
        if '#delivery-type' in payload:
            configs.append(payload['#delivery-type']['Magento_Ui/js/core/app']['components']['deliveryType']['data'])
    if len(configs) != 1:
        raise ValueError('Missing or ambiguous Rockler delivery identity')
    config = configs[0]
    # Bundles/grouped pages require a configuration-specific price and destination.
    if config.get('productType') != 'simple':
        return {'supported': False, 'type': config.get('productType')}
    uid, sku = str(config.get('id', '')), str(config.get('sku', ''))
    if not uid.isdigit() or not sku.isdigit():
        raise ValueError('Malformed Rockler SKU identity')
    products = [json.loads(s.get_text()) for s in soup.select('script[type="application/ld+json"]')]
    products = [p for p in products if isinstance(p, dict) and p.get('@type') == 'Product']
    if len(products) != 1 or str(products[0].get('sku')) != sku:
        raise ValueError('Rockler structured SKU mismatch')
    product = products[0]
    heading = soup.select_one('h1')
    name = text(product.get('name'))
    if not heading or heading.get_text(' ', strip=True) != name or text(config.get('name')) != name:
        raise ValueError('Rockler product name mismatch')
    offers = product.get('offers')
    if not isinstance(offers, list) or len(offers) != 1:
        raise ValueError('Ambiguous Rockler structured price')
    offer = offers[0]
    if offer.get('priceCurrency') != 'USD' or product_url(offer.get('url', '')) != url:
        raise ValueError('Rockler currency or destination mismatch')
    values = {}
    for price_type, prefix in [('finalPrice', 'product-price-'), ('oldPrice', 'old-price-')]:
        nodes = soup.select(f'.product-info-main [data-price-type="{price_type}"][id="{prefix}{uid}"]')
        parsed = {amount(n.get('data-price-amount')) for n in nodes}
        if not nodes and price_type == 'oldPrice':
            values[price_type] = None
            continue
        if len(parsed) != 1 or any(parse_price(n.get_text(' ', strip=True)) not in parsed for n in nodes):
            raise ValueError('Ambiguous Rockler displayed price')
        values[price_type] = parsed.pop()
    if amount(offer.get('price')) != values['finalPrice']:
        raise ValueError('Rockler structured and visible price disagree')
    brands = [row.select_one('td').get_text(' ', strip=True)
              for row in soup.select('#product-attribute-specs-table tr')
              if row.select_one('th') and row.select_one('td')
              and row.select_one('th').get_text(' ', strip=True) == 'Brand']
    image = product.get('image') or []
    return {'supported': True, 'uid': uid, 'sku': sku, 'name': name, 'url': url,
            'price': values['finalPrice'], 'reference': values['oldPrice'],
            'condition': offer.get('itemCondition'), 'schema_availability': offer.get('availability'),
            'brand': brands[0] if len(set(brands)) == 1 else None,
            'category': ' / '.join(n.get_text(' ', strip=True) for n in soup.select('.breadcrumbs li')[:-1]),
            'image': image[0].get('url') if image and isinstance(image[0], dict) else None}


def stock_url(data: dict) -> str:
    if not data.get('supported') or not str(data.get('uid', '')).isdigit():
        raise ValueError('Rockler delivery requires a bound product ID')
    return ORIGIN + '/frx/stockmessage?' + urlencode({'pid': data['uid'], 'timezone': 'UTC'})


def discounted_product(data: dict) -> bool:
    return (data['supported'] and data['condition'] == 'https://schema.org/NewCondition'
            and data['reference'] is not None and 0 < data['price'] < data['reference'])


def delivery_data(raw: dict) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get('delivery_available'), bool):
        raise TypeError('Missing Rockler delivery evidence')
    message = text(raw.get('delivery_box_message'))
    estimate = text(raw.get('estimate_shipping_message'))
    terms = [text(raw.get(k)) for k in ('special_shipping_message', 'extra_shipping_cost_message')]
    available = raw['delivery_available'] and raw.get('is_stop_order') != 1
    ready = (available and raw.get('direct_ship') == 0 and raw.get('is_stop_order') == 0
             and message == 'Ready to Ship' and text(raw.get('stock_message')) == 'In Stock and Ready to Ship'
             and not estimate)
    # backorder_date alone is also populated for ready-to-ship SKUs. The storefront
    # renders estimate_shipping_message, so preserve that active notice instead.
    notes = list(dict.fromkeys(v for v in ([message] if not ready else []) + [estimate] + terms if v))
    return {'available': available, 'availability': 'in_stock' if ready else 'unknown',
            'note': ' · '.join(notes), 'message': message, 'estimate': estimate,
            'direct_ship': raw.get('direct_ship')}


class RocklerParser(BaseParser):
    requires_product_pages = True

    def __init__(self):
        self._page = 0
        self._total = None
        self._seen = set()

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        raw = json.loads(html)
        # Broad secondary category tags can call a real bandsaw an accessory.
        # Discovery uses the title; the product breadcrumb supplies final taxonomy.
        return [Product(name=unescape(row['name']), url=product_url(row['url']),
                        current_price=0, brand=unescape(row.get('brand') or '')) for row in raw['results']]

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        parts = urlsplit(current_url)
        params = parse_qs(parts.query)
        page = int(params.get('page', ['1'])[0])
        if current_url != listing_url(page):
            raise ValueError('Unexpected Rockler category request')
        raw = json.loads(html)
        meta, rows = raw['pagination'], raw['results']
        if raw.get('merchandising', {}).get('content', {}).get('inline'):
            raise ValueError('Rockler banners must not count as products')
        total, size = meta['totalResults'], meta['perPage']
        if (isinstance(total, bool) or not isinstance(total, int) or not 0 <= total <= 5000
                or size != 24 or meta['currentPage'] != page
                or meta['totalPages'] != math.ceil(total / size)):
            raise ValueError('Invalid Rockler pagination metadata')
        if page == 1:
            self._page, self._total, self._seen = 0, total, set()
        if page != self._page + 1 or total != self._total:
            raise ValueError('Rockler catalog changed during traversal')
        expected = min(size, max(0, total - (page - 1) * size))
        keys = [str(row['uid']) for row in rows]
        if (len(rows) != expected or len(set(keys)) != len(keys) or self._seen.intersection(keys)
                or any(not key.isdigit() for key in keys)
                or meta['begin'] != (page - 1) * size + 1 or meta['end'] != (page - 1) * size + expected):
            raise ValueError('Missing or repeated Rockler listings')
        self._seen.update(keys)
        self._page = page
        terminal = len(self._seen) == total
        if meta['nextPage'] != (0 if terminal else page + 1):
            raise ValueError('Rockler next-page mismatch')
        return None if terminal else listing_url(page + 1)

    def get_product_evidence_url(self, html: str, page_url: str) -> str | None:
        data = detail_data(html, page_url)
        # Sale categories also contain full-price free-gift promotions. Their
        # product pages establish that no percentage discount needs stock checks.
        return stock_url(data) if discounted_product(data) else None

    def parse_product_page(self, html: str, page_url: str) -> list[Product]:
        if discounted_product(detail_data(html, page_url)):
            raise ValueError('Rockler delivery evidence required')
        return []

    def parse_product_evidence(self, html: str, page_url: str, evidence: str) -> list[Product]:
        data = detail_data(html, page_url)
        delivery = delivery_data(json.loads(evidence))
        if not discounted_product(data) or not delivery['available']:
            return []
        offer = VariantOffer(variant_key=f"{data['sku']}|{data['uid']}|{urlsplit(page_url).path}",
                             url=page_url, current_price=data['price'], original_price=data['reference'],
                             options=f"SKU {data['sku']}", availability=delivery['availability'],
                             availability_note=delivery['note'], image_url=data['image'])
        return [Product(name=data['name'], url=page_url, current_price=data['price'],
                        original_price=data['reference'], brand=data['brand'], product_type=data['category'],
                        image_url=data['image'], offers=[offer])]
