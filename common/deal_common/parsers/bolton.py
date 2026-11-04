"""Bolton's visible single-SKU purchase cards, with strict category reconciliation."""
import math
import re
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.base import BaseParser
from deal_common.parsers.common import parse_price

HOST = 'www.boltontool.com'


def offer_destination(url: str, key: str) -> bool:
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    fields = key.split('|')
    return (parts.scheme == 'https' and parts.netloc == HOST and not parts.query and not parts.fragment
            and len(fields) == 3 and fields[0].isdigit()
            and bool(re.fullmatch(r'[A-Za-z0-9._-]+', fields[1]))
            and bool(re.fullmatch(r'[A-Za-z0-9_-]+', fields[2]))
            and parts.path == '/' + fields[2])


def _price(value: str) -> float:
    if not re.fullmatch(r'\$?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?', value.strip()):
        raise ValueError('Invalid Bolton price')
    number = parse_price(value)
    if number is None or not math.isfinite(number) or number <= 0:
        raise ValueError('Invalid Bolton price')
    return number


def _one(values, label):
    values = list(values)
    if not values or any(not value for value in values) or len(set(values)) != 1:
        raise ValueError('Missing or conflicting Bolton ' + label)
    return values[0]


def detail_data(html: str, page_url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    # The live notice overrides generic InStock metadata. A past restoration
    # date does not establish that the restriction has actually been removed.
    # Optional freight controls do not prove this particular SKU is LTL.
    if any(n.get_text(' ', strip=True) for n in soup.select('.warehouse-relocation-banner')):
        raise ValueError('Unresolved Bolton warehouse shipping restriction')
    canonical = _one((n.get('href') for n in soup.select('link[rel=canonical]')), 'canonical')
    incoming, target = urlsplit(page_url), urlsplit(canonical)
    if (incoming.scheme != 'https' or incoming.netloc != HOST or target.netloc != HOST
            or incoming.path.rsplit('/', 1)[-1] != target.path.rsplit('/', 1)[-1]):
        raise ValueError('Bolton canonical identity mismatch')
    scopes = soup.select('[itemscope][itemtype="https://schema.org/Product"]')
    if len(scopes) != 1:
        raise ValueError('Ambiguous Bolton product schema')
    scope = scopes[0]

    def prop(name, attribute='content'):
        return _one((n.get(attribute) for n in scope.select(f'[itemprop="{name}"]')), name)

    sku, name = prop('sku'), prop('name')
    product_id = _one((n.get('value') for n in soup.select('#product input[name="product_id"]')), 'product ID')
    key = '|'.join((product_id, sku, target.path.lstrip('/')))
    if not offer_destination(canonical, key):
        raise ValueError('Unsupported Bolton SKU destination')
    visible_name = _one((n.get_text(' ', strip=True) for n in soup.select('#content .product-detail-title')), 'title')
    models = [n.select_one('strong').get_text(' ', strip=True) for n in soup.select('#content li')
              if n.get_text(' ', strip=True).startswith('Model #:') and n.select_one('strong')]
    if name != visible_name or _one(models, 'model') != sku:
        raise ValueError('Bolton visible and structured identity disagree')
    if prop('priceCurrency') != 'USD':
        raise ValueError('Bolton currency is not USD')
    price = _price(_one((n.get_text(' ', strip=True) for n in soup.select('.product-detail-price__current')), 'sale price'))
    if _price(prop('price')) != price:
        raise ValueError('Bolton structured and visible prices disagree')
    references = soup.select('.product-detail-price__old')
    reference = _price(_one((n.get_text(' ', strip=True) for n in references), 'reference')) if references else None
    stock_nodes = soup.select('.product-detail-stock')
    if len(stock_nodes) != 1:
        raise ValueError('Missing Bolton purchase stock')
    stock_text = stock_nodes[0].get_text(' ', strip=True).casefold()
    state = prop('availability', 'href')
    stock = (state == 'https://schema.org/InStock' and stock_text == 'in stock'
             and 'product-detail-stock--in_stock' in stock_nodes[0].get('class', []))
    condition = prop('itemCondition', 'href').removeprefix('https://schema.org/')
    if soup.select('#product [name^="option["]'):
        raise ValueError('Unresolved Bolton product options')
    quantities = soup.select('#product input[name="quantity"]')
    if (len(quantities) != 1 or quantities[0].get('value') != '1'
            or quantities[0].get('min', '1') != '1'):
        raise ValueError('Bolton price requires unsupported quantity')
    carts = soup.select('#product #button-cart')
    if len(carts) != 1 or carts[0].has_attr('disabled') or carts[0].get('aria-disabled') == 'true':
        raise ValueError('Bolton purchase control is unavailable')
    breadcrumbs = [a.get_text(' ', strip=True) for a in soup.select('.breadcrumb a')]
    freight = 'Optional Freight Delivery Services' in soup.select_one('#content').get_text(' ', strip=True)
    return {'url': canonical, 'variant_key': key, 'sku': sku, 'name': name, 'price': price,
            'reference': reference, 'currency': 'USD', 'in_stock': stock, 'condition': condition,
            'options': 'Model ' + sku, 'image': prop('image'), 'category': ' > '.join(breadcrumbs),
            'shipping_note': ('Freight delivery services may add charges. Confirm residential, lift-gate and unloading requirements.' if freight else '')}


class BoltonParser(BaseParser):
    requires_product_pages = True

    def __init__(self):
        self.collection = ''
        self.seen: set[str] = set()
        self.total: int | None = None
        self.pages: int | None = None
        self.last_url = ''
        self.next_url: str | None = None

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        parts = urlsplit(page_url)
        if parts.scheme != 'https' or parts.netloc != HOST:
            raise ValueError('Unsafe Bolton category')
        query = parse_qs(parts.query)
        if len(query.get('page', ['1'])) != 1:
            raise ValueError('Ambiguous Bolton page')
        page = int(query.get('page', ['1'])[0])
        if page < 1:
            raise ValueError('Invalid Bolton page')
        if page == 1:
            self.collection, self.seen, self.total, self.pages = parts.path, set(), None, None
        elif parts.path != self.collection or page_url != self.next_url:
            raise ValueError('Unexpected Bolton page')
        soup = BeautifulSoup(html, 'html.parser')
        summaries = soup.select('.col-sm-6.text-right')
        summary = _one((n.get_text(' ', strip=True) for n in summaries), 'category count')
        match = re.fullmatch(r'Showing (\d+) to (\d+) of (\d+) \((\d+) Pages\)', summary)
        if not match:
            raise ValueError('Missing Bolton pagination count')
        start, end, total, pages = map(int, match.groups())
        cards = soup.select('#content .product-thumb')
        expected = end - start + 1 if total else 0
        if (not 1 <= page <= max(pages, 1) or (total and (pages < 1 or not start <= end <= total))
                or len(cards) != expected or (total and start != len(self.seen) + 1)
                or (not total and (start or end)) or (self.total is not None and self.total != total)
                or (self.pages is not None and self.pages != pages)):
            raise ValueError('Incomplete or changing Bolton category')
        products = []
        for card in cards:
            link = card.select_one('h5 a') or card.select_one('h4 a')
            if link is None:
                raise ValueError('Missing Bolton listing link')
            target = urlsplit(link['href'])
            slug = target.path.rsplit('/', 1)[-1]
            if (target.scheme != 'https' or target.netloc != HOST or target.query or target.fragment
                    or not re.fullmatch(r'[A-Za-z0-9_-]+', slug) or slug in self.seen):
                raise ValueError('Unsafe or repeated Bolton product')
            self.seen.add(slug)
            sale, old = card.select_one('.price-new'), card.select_one('.price-old')
            if sale is None or old is None or 'In stock' not in card.get_text(' ', strip=True):
                continue
            price, reference = _price(sale.get_text()), _price(old.get_text())
            if price >= reference:
                continue
            products.append(Product(name=link.get_text(' ', strip=True),
                                    url=f'https://{HOST}{target.path}', current_price=price,
                                    original_price=reference))
        self.total, self.pages = total, pages
        next_nodes = [a for a in soup.select('ul.pagination a') if a.get_text(' ', strip=True) == '>']
        if len(next_nodes) != int(page < pages) or (page >= pages and len(self.seen) != total):
            raise ValueError('Unreconciled Bolton terminal page')
        self.next_url = next_nodes[0].get('href') if next_nodes else None
        if self.next_url:
            next_parts = urlsplit(self.next_url)
            if (next_parts.scheme != 'https' or next_parts.netloc != HOST or next_parts.path != self.collection
                    or parse_qs(next_parts.query).get('page') != [str(page + 1)]):
                raise ValueError('Unexpected Bolton next page')
        self.last_url = page_url
        return products

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        if current_url != self.last_url:
            raise ValueError('Bolton page not validated')
        return self.next_url

    def parse_product_page(self, html: str, page_url: str) -> list[Product]:
        row = detail_data(html, page_url)
        if (not row['in_stock'] or row['condition'] != 'NewCondition'
                or row['reference'] is None or row['price'] >= row['reference']):
            return []
        offer = VariantOffer(variant_key=row['variant_key'], url=row['url'],
                             current_price=row['price'], original_price=row['reference'],
                             options=row['options'], availability='in_stock', image_url=row['image'],
                             availability_note=row['shipping_note'])
        return [Product(name=row['name'], url=row['url'], current_price=row['price'],
                        original_price=row['reference'], image_url=row['image'],
                        product_type=row['category'], offers=[offer])]
