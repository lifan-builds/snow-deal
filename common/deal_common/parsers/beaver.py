"""Beaver's Shopify prices with its main purchase panel's stock evidence."""
import json
import math
import re
from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.parsers.common import parse_price
from deal_common.parsers.shopify import ShopifyParser

HOST = 'beavertools.com'


def _one(values, label):
    values = list(values)
    if len(values) != 1 or values[0] is None:
        raise ValueError('Missing or ambiguous Beaver ' + label)
    return values[0]


def _money(value):
    text = str(value).strip()
    if not re.fullmatch(r'\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?', text):
        raise ValueError('Invalid Beaver price')
    price = parse_price(text)
    if price is None or not math.isfinite(price) or price <= 0:
        raise ValueError('Invalid Beaver price')
    return price


def _minor(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError('Invalid Beaver minor-unit price')
    return value / 100


def detail_data(html: str, page_url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    parts = urlsplit(page_url)
    if parts.scheme != 'https' or parts.netloc != HOST or not parts.path.startswith('/products/'):
        raise ValueError('Unsafe Beaver product URL')
    canonical = _one((n.get('href') for n in soup.select('link[rel="canonical"]')), 'canonical')
    if canonical != f'https://{HOST}{parts.path}':
        raise ValueError('Beaver canonical identity mismatch')
    main = _one(soup.select('product-info[id^="MainProduct-"]'), 'purchase panel')
    if main.get('data-url') != parts.path:
        raise ValueError('Beaver purchase path mismatch')
    product_id = main.get('data-product-id', '')
    if not product_id.isdigit():
        raise ValueError('Invalid Beaver product ID')
    name = _one((n.get_text(' ', strip=True) for n in main.select('h1.product__title')), 'title')
    sku = _one((n.get_text(' ', strip=True) for n in main.select('.product__sku > span:last-child')), 'SKU')
    form = _one(main.select('form.main-product-form[action="/cart/add"]'), 'purchase form')
    key = _one((n.get('value') for n in form.select('input[name="id"]')), 'variant')
    if not key.isdigit() or _one((n.get('value') for n in form.select('input[name="product-id"]')), 'form product') != product_id:
        raise ValueError('Beaver purchase identity mismatch')
    requested = parse_qs(parts.query).get('variant')
    if requested is not None and requested != [key]:
        raise ValueError('Beaver selected variant mismatch')
    quantity = _one(form.select('input[name="quantity"]'), 'quantity')
    if quantity.get('value') != '1' or quantity.get('min') != '1' or quantity.get('step') != '1':
        raise ValueError('Unsupported Beaver quantity')
    button = _one(form.select('button[name="add"]'), 'purchase button')
    literals = []
    for script in main.select('script:not([src])'):
        text = script.get_text()
        for match in re.finditer(r'\bwindow\.dpoData\s*=\s*\{\s*product\s*:\s*', text):
            value, _ = json.JSONDecoder().raw_decode(text[match.end():].lstrip())
            literals.append(value)
    raw = _one(literals, 'product data')
    if (not isinstance(raw, dict) or str(raw.get('id')) != product_id or raw.get('title') != name
            or '/products/' + str(raw.get('handle')) != parts.path):
        raise ValueError('Beaver product literal identity mismatch')
    variants = raw.get('variants')
    if not isinstance(variants, list) or len(variants) != 1 or not isinstance(variants[0], dict):
        raise ValueError('Unsupported Beaver multiple variants')
    variant = variants[0]
    if (str(variant.get('id')) != key or variant.get('sku') != sku
            or variant.get('requires_selling_plan') is not False
            or variant.get('quantity_rule', {}).get('min') != 1
            or variant.get('quantity_rule', {}).get('increment') != 1):
        raise ValueError('Beaver variant or quantity identity mismatch')
    if variant.get('options') != ['Default Title']:
        raise ValueError('Unresolved Beaver product options')
    schema = _one((json.loads(n.get_text()) for n in main.select('script[type="application/ld+json"]')), 'product schema')
    offer_url = canonical + '?variant=' + key
    if not isinstance(schema, dict) or schema.get('@type') != 'Product':
        raise ValueError('Invalid Beaver product schema')
    offer = schema.get('offers')
    if (not isinstance(offer, dict) or schema.get('name') != name or schema.get('sku') != sku
            or schema.get('url') != canonical or offer.get('url') != offer_url
            or offer.get('priceCurrency') != 'USD'):
        raise ValueError('Beaver structured identity or currency mismatch')
    price_box = _one(main.select('.product__block--price'), 'price panel')
    price = _money(_one((n.get_text(' ', strip=True) for n in price_box.select('.f-price__sale .f-price-item--sale')), 'sale price'))
    reference = _money(_one((n.get_text(' ', strip=True) for n in price_box.select('.f-price__sale .f-price-item--regular')), 'reference'))
    if price != _money(offer.get('price')) or price != _minor(variant.get('price')) or reference != _minor(variant.get('compare_at_price')):
        raise ValueError('Beaver visible and structured prices disagree')
    label = _one((n.get_text(' ', strip=True) for n in main.select('.vendor-stock-label')), 'stock label')
    sold_out = (variant.get('available') is False
                or offer.get('availability', '').rsplit('/', 1)[-1] in {'OutOfStock', 'SoldOut', 'Discontinued'}
                or label.casefold() in {'out of stock', 'sold out', 'discontinued'})
    in_stock = (not sold_out and label == 'In Stock' and variant.get('available') is True and not button.has_attr('disabled')
                and offer.get('availability', '').rsplit('/', 1)[-1] == 'InStock')
    note = '' if in_stock else label
    return {'url': canonical, 'name': name, 'sku': sku, 'product_id': product_id,
            'variant_key': key, 'price': price, 'reference': reference, 'currency': 'USD',
            'in_stock': in_stock, 'shipping_note': note, 'stock_label': label,
            'available': variant.get('available') is True, 'sold_out': sold_out, 'options': ''}


class BeaverShopifyParser(ShopifyParser):
    requires_product_pages = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products: dict[str, Product] = {}

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        products = super().parse_listing_page(html, page_url)
        self.products.update({product.url: product for product in products})
        return products

    def parse_product_page(self, html: str, page_url: str) -> list[Product]:
        actual = detail_data(html, page_url)
        product = self.products.get(page_url)
        if product is None or len(product.offers) != 1:
            raise ValueError('Missing or ambiguous Beaver discovery offer')
        offer = product.offers[0]
        if (product.name != actual['name'] or offer.variant_key != actual['variant_key']
                or offer.current_price != actual['price'] or offer.original_price != actual['reference']
                or offer.options != actual['options']):
            raise ValueError('Beaver listing and purchase panel disagree')
        if actual['sold_out']:
            return []
        selected = replace(offer, availability='in_stock' if actual['in_stock'] else 'unknown',
                           availability_note=actual['shipping_note'])
        return [replace(product, offers=[selected])]
