"""Bike Closet's public WooCommerce parent/variation and storefront evidence."""
import json
import math
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer, size_key
from deal_common.parsers.base import BaseParser

ORIGIN = 'https://bikecloset.com'
API = ORIGIN + '/wp-json/wc/store/v1/products'
CATEGORY = '3411'


def listing_url(page=1):
    return API + '?' + urlencode({'category': CATEGORY, 'type': 'variable', 'per_page': 100,
                                 'page': page, 'orderby': 'id', 'order': 'asc'})


def text(value):
    value = BeautifulSoup(value or '', 'html.parser').get_text(' ', strip=True)
    return re.sub(r'\s+', ' ', value).strip().translate(str.maketrans({'’': "'", '‘': "'"}))


def product_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'bikecloset.com' or p.fragment
            or not re.fullmatch(r'/product/[a-z0-9-]+/', p.path)):
        raise ValueError('Invalid Bike Closet product destination')
    return urlunsplit((p.scheme, p.netloc, p.path, '', ''))


def offer_destination(url, key):
    try:
        product_url(url)
        identity, query = key.split('|')
        parent, variant = identity.split(':')
        pairs = parse_qsl(urlsplit(url).query, keep_blank_values=True)
        return (parent.isdigit() and variant.isdigit() and int(parent) > 0 and int(variant) > 0
                and bool(pairs) and len(dict(pairs)) == len(pairs)
                and all(re.fullmatch(r'attribute_[a-z0-9_]+', k) and v for k, v in pairs)
                and urlencode(sorted(pairs)) == query)
    except (ValueError, AttributeError):
        return False


def new_condition(parent):
    description = text(parent.get('short_description')).casefold()
    return (bool(re.search(r'\b(?:brand new|new in box|new old stock)\b', description))
            and not re.search(r'\b(?:used|refurbished|reconditioned|open.box|blemished|demo)\b',
                              parent['name'].casefold() + ' ' + description))


def product_kind(parent):
    name, description = unescape(parent['name']).casefold(), text(parent.get('short_description')).casefold()
    if 'frameset' in name or 'frames are final sale' in description:
        return 'Framesets'
    if 'complete bike' in name:
        return 'Complete Bikes'
    return ''


def manufacturer(parent):
    names = {'look': 'LOOK', 'time frames': 'TIME'}
    brands = {names[c['name'].casefold()] for c in parent['categories'] if c['name'].casefold() in names}
    return next(iter(brands)) if len(brands) == 1 else None


def size_consistent(name, size):
    explicit = re.findall(r'\bSIZE\s+(XXS|XS|S|M|L|XL|XXL)\b', name, re.IGNORECASE)
    return not explicit or (bool(size) and all(size_key(s) == size_key(size) for s in explicit))


def selection(parent, variant_id):
    matches = [v for v in parent['variations'] if v['id'] == variant_id]
    if len(matches) != 1:
        raise ValueError('Missing or repeated Bike Closet variation')
    definitions = {a['name']: a for a in parent['attributes'] if a.get('has_variations') is True}
    attributes = matches[0]['attributes']
    if len(attributes) != len(definitions) or len({a['name'] for a in attributes}) != len(attributes):
        raise ValueError('Incomplete Bike Closet option selection')
    query, labels = {}, {}
    for a in attributes:
        definition = definitions[a['name']]
        terms = [t for t in definition['terms'] if t['slug'] == a['value']]
        if not a['value'] or len(terms) != 1 or not re.fullmatch(r'pa_[a-z0-9_]+', definition['taxonomy']):
            raise ValueError('Ambiguous Bike Closet attribute')
        query['attribute_' + definition['taxonomy']] = a['value']
        labels[a['name']] = unescape(terms[0]['name'])
    return urlencode(sorted(query.items())), labels


def notices(parent, labels):
    description = text(parent.get('short_description'))
    # Preserve dates as written: an old-looking estimate is not proof of arrival.
    estimates = re.findall(r'(?:Size\s+[^.!?]+?\s+)?[Ww]ill ship to you[^.!?]+[.!?]?', description)
    delayed = []
    for sentence in estimates:
        scope = re.match(r'Size\s+(\w+)(?:\s+(.+?))?\s+will ship to you', sentence, re.IGNORECASE)
        if scope:
            size, color = scope.group(1), scope.group(2)
            sizes = {size_key(t['name']) for a in parent['attributes'] if a['name'] == 'Size' for t in a['terms']}
            colors = {t['name'] for a in parent['attributes'] if a['name'] == 'Color' for t in a['terms']}
            # A merchant qualifier such as Rose binds only to one explicit term,
            # e.g. V46 Rose. Missing/ambiguous mappings cannot exempt any variant.
            color_matches = [c for c in colors if color and re.search(r'(?:^|\s)' + re.escape(color) + '$', c, re.IGNORECASE)]
            has_size = 'Size' in labels and size_key(size) in sizes
            has_color = not color or ('Color' in labels and len(color_matches) == 1)
            if has_size and has_color:
                if size_key(size) != size_key(labels['Size']):
                    continue
                if color and color_matches[0].casefold() != labels['Color'].casefold():
                    continue
        delayed.append(sentence)
    notes = list(delayed)
    notes.extend(re.findall(r'(?:Cannot|Can not|Does not|Will not) ship[^.!?]+[.!?]?', description, re.IGNORECASE))
    if re.search(r'\bfinal sale\b', description, re.IGNORECASE):
        notes.append('Final sale.')
    if product_kind(parent) == 'Framesets' and re.search(r'photos? show a complete bike', text(parent.get('description')), re.IGNORECASE):
        notes.append('Frameset only; retailer photo may show a complete bike.')
    return bool(delayed), ' · '.join(notes)


def money(prices, field):
    if prices.get('currency_code') != 'USD' or type(prices.get('currency_minor_unit')) is not int or prices['currency_minor_unit'] != 2:
        raise ValueError('Bike Closet currency is not explicit USD cents')
    value = prices[field]
    if not isinstance(value, str) or not value.isdigit():
        raise ValueError('Malformed Bike Closet price')
    amount = int(value) / 100
    if not math.isfinite(amount):
        raise ValueError('Nonfinite Bike Closet price')
    return amount


def image_url(images):
    if not images:
        return None
    first = images[0]
    candidates = [(int(width), url) for url, width in re.findall(r'(https://[^,\s]+)\s+(\d+)w', first.get('srcset', ''))
                  if int(width) >= 600]
    return min(candidates)[1] if candidates else first.get('src') or first.get('thumbnail')


def decode_offer(parent, variant):
    if (parent['type'] != 'variable' or parent.get('parent') != 0 or variant['type'] != 'variation'
            or variant['parent'] != parent['id'] or text(variant['name']) != text(parent['name'])):
        raise ValueError('Bike Closet parent/variant identity mismatch')
    query, labels = selection(parent, variant['id'])
    url = product_url(parent['permalink']) + '?' + query
    key = f"{parent['id']}:{variant['id']}|{query}"
    if (product_url(variant['permalink']) != product_url(parent['permalink'])
            or not offer_destination(variant['permalink'], key)):
        raise ValueError('Bike Closet selected destination mismatch')
    for flag in ('is_in_stock', 'is_purchasable', 'is_on_backorder'):
        if type(variant.get(flag)) is not bool:
            raise ValueError('Unknown Bike Closet stock or purchase status')
    price, reference = money(variant['prices'], 'price'), money(variant['prices'], 'regular_price')
    if (not new_condition(parent) or not 0 < price < reference or not variant['is_in_stock']
            or not variant['is_purchasable'] or variant['is_on_backorder']
            or not size_consistent(parent['name'], labels.get('Size'))):
        return None
    delayed, note = notices(parent, labels)
    options = [f'{k}: {v}' for k, v in sorted(labels.items())]
    if variant.get('sku'):
        options.append('SKU ' + variant['sku'])
    return VariantOffer(variant_key=key, url=url, current_price=price, original_price=reference,
                        size=labels.get('Size'), options=' / '.join(options),
                        availability='unknown' if delayed else 'in_stock', availability_note=note,
                        image_url=image_url(variant.get('images')))


def validate_detail(html, parent):
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select_one('link[rel=canonical]')
    form = soup.select_one('form.variations_form')
    if (not canonical or canonical.get('href') != parent['permalink'] or not form
            or form.get('data-product_id') != str(parent['id']) or form.get('action') != parent['permalink']):
        raise ValueError('Bike Closet storefront identity mismatch')
    products = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = json.loads(script.get_text())
        products.extend(p for p in raw.get('@graph', [raw]) if p.get('@type') == 'Product')
    if (len(products) != 1 or products[0]['url'] != parent['permalink']
            or text(products[0]['name']) != text(parent['name'])
            or str(products[0]['sku']) != str(parent.get('sku') or parent['id'])
            or not products[0]['offers']
            or any(o.get('priceCurrency') != 'USD' for o in products[0]['offers'])):
        raise ValueError('Bike Closet storefront product evidence mismatch')
    if text(products[0]['description']) != text(parent['short_description']):
        raise ValueError('Bike Closet condition or shipping description changed')
    return form


class BikeClosetParser(BaseParser):
    requires_product_pages = True

    def __init__(self):
        self.parents = {}
        self._seen = set()
        self._page = 0
        self._total = None
        self._validated_url = None
        self._next = None

    def validate_listing_response(self, html, page_url, headers):
        params = dict(parse_qsl(urlsplit(page_url).query))
        page = int(params['page'])
        if page_url != listing_url(page):
            raise ValueError('Unexpected Bike Closet listing URL')
        total, pages = int(headers['x-wp-total']), int(headers['x-wp-totalpages'])
        if not 0 <= total <= 5000 or pages != math.ceil(total / 100):
            raise ValueError('Invalid Bike Closet pagination totals')
        if page == 1:
            self._seen, self._page, self._total = set(), 0, total
        rows = json.loads(html)
        ids = [r['id'] for r in rows]
        if (page != self._page + 1 or total != self._total or len(rows) != min(100, max(0, total - (page - 1) * 100))
                or len(set(ids)) != len(ids) or self._seen.intersection(ids)
                or any(type(i) is not int or i <= 0 for i in ids)
                or any(r['type'] != 'variable' or r.get('parent') != 0 for r in rows)):
            raise ValueError('Truncated, repeated or changed Bike Closet listing')
        self._seen.update(ids)
        self._page, self._validated_url = page, page_url
        self._next = None if len(self._seen) == total else listing_url(page + 1)

    def parse_listing_page(self, html, page_url):
        rows = json.loads(html)
        self.parents.update({product_url(p['permalink']): p for p in rows})
        return [Product(name=unescape(p['name']), url=product_url(p['permalink']), current_price=0,
                        product_type=product_kind(p)) for p in rows]

    def get_next_page_url(self, html, current_url):
        if current_url != self._validated_url:
            raise ValueError('Bike Closet pagination headers required')
        return self._next

    def get_product_evidence_url(self, html, page_url):
        parent = self.parents[page_url]
        validate_detail(html, parent)
        ids = [v['id'] for v in parent['variations']]
        if not 1 <= len(ids) <= 100 or len(set(ids)) != len(ids) or any(type(i) is not int or i <= 0 for i in ids):
            raise ValueError('Unsupported Bike Closet variation count')
        return API + '?' + urlencode({'type': 'variation', 'include': ','.join(map(str, sorted(ids))), 'per_page': 100})

    def parse_product_evidence(self, html, page_url, evidence):
        parent = self.parents[page_url]
        validate_detail(html, parent)
        variants = json.loads(evidence)
        ids = [v['id'] for v in variants]
        if len(set(ids)) != len(ids) or set(ids) != {v['id'] for v in parent['variations']}:
            raise ValueError('Incomplete Bike Closet variation response')
        offers = [offer for v in variants if (offer := decode_offer(parent, v)) is not None]
        if not offers:
            return []
        best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
        return [Product(name=unescape(parent['name']), url=page_url, current_price=best.current_price,
                        original_price=best.original_price, brand=manufacturer(parent),
                        product_type=product_kind(parent), image_url=best.image_url, offers=offers)]
