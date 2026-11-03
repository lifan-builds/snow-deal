"""Taylor Toolworks public listing HTML and exact-SKU JSON literals."""
import json
import math
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer
from deal_common.parsers.base import BaseParser
from deal_common.parsers.common import parse_price


def product_url(value: str) -> str:
    parts = urlsplit(value)
    if (parts.scheme != 'https' or parts.netloc != 'taytools.com'
            or not re.fullmatch(r'/[a-z0-9][a-z0-9_;-]+', parts.path)):
        raise ValueError('Invalid Taylor product URL')
    return urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))


def literal(script: str, name: str):
    matches = list(re.finditer(r'\bconst\s+' + re.escape(name) + r'\s*=\s*', script))
    if len(matches) != 1:
        raise ValueError(f'Missing or ambiguous Taylor {name}')
    remainder = script[matches[0].end():]
    value, end = json.JSONDecoder().raw_decode(remainder)
    if not remainder[end:].lstrip().startswith(';'):
        raise ValueError(f'Taylor {name} is not a JSON literal assignment')
    return value


def sku_selection(record: dict, keys: list, mapping: dict | list) -> dict:
    selection = {}
    for key in keys:
        if not isinstance(key, str) or not re.fullmatch(r'a_\d+', key):
            raise ValueError('Unknown Taylor option key')
        value = record.get(key)
        if not isinstance(value, str) or not re.fullmatch(r'v_\d+', value):
            raise ValueError('Unknown Taylor option value')
        parameter = next((field for field in ('color', 'size_x', 'size_y', 'size_z')
                          if isinstance(mapping, dict) and mapping.get(field) == key), key)
        if parameter in selection:
            raise ValueError('Ambiguous Taylor option mapping')
        selection[parameter] = value
    return dict(sorted(selection.items()))


def offer_destination(url: str, variant_key: str) -> bool:
    """The opaque identity retains SKU and the exact selector query together."""
    try:
        product_url(url)
        sku, separator, expected_query = variant_key.partition('|')
        if not separator or not sku.isdigit() or urlsplit(url).fragment:
            return False
        pairs = parse_qsl(urlsplit(url).query, keep_blank_values=True)
        if any(not re.fullmatch(r'(?:a_\d+|color|size_[xyz])', key)
               or not re.fullmatch(r'v_\d+', value) for key, value in pairs):
            return False
        return len(dict(pairs)) == len(pairs) and urlencode(sorted(pairs)) == expected_query
    except ValueError:
        return False


def detail_data(html: str, url: str) -> dict:
    """Decode facts without evaluating JavaScript or trusting parent-listing IDs."""
    soup = BeautifulSoup(html, 'html.parser')
    scripts = '\n'.join(s.get_text() for s in soup.select('script:not([src])'))
    title = soup.select_one('#title')
    canonical = soup.select_one('link[rel="canonical"]')
    if (not title or not canonical or product_url(canonical.get('href', '')) != product_url(url)
            or not soup.select_one('#price.us_only')):
        raise ValueError('Taylor identity or US price container missing')
    records, keys, mapping = (literal(scripts, name) for name in ('skusKeyValues', 'keys', 'sc'))
    if not isinstance(records, dict) or not records or not isinstance(keys, list) or not isinstance(mapping, (dict, list)):
        raise ValueError('Malformed Taylor SKU data')
    selections = set()
    rows = {}
    for sku, record in records.items():
        if not sku.isdigit() or not isinstance(record, dict) or not isinstance(record.get('data'), dict):
            raise ValueError('Malformed Taylor SKU')
        selection = sku_selection(record, keys, mapping)
        query = urlencode(selection)
        if query in selections:
            raise ValueError('Multiple Taylor SKUs share a destination')
        selections.add(query)
        options = []
        for key in keys:
            option = soup.select_one(f'[data-key="{key}"] option[value="{record[key]}"]')
            if not option:
                raise ValueError('Missing Taylor option description')
            options.append(option.get_text(' ', strip=True))
        data = record['data']
        if not data.get('vendor_sku'):
            raise ValueError('Missing Taylor merchant SKU')
        rows[sku] = {**data, 'selection': selection, 'query': query,
                     'options': ' / '.join([f"SKU {data['vendor_sku']}", *options])}
    crumbs = soup.select('[itemprop="itemListElement"]')
    brand_match = re.search(r'\bitem_brand\s*:\s*', scripts)
    brand = json.JSONDecoder().raw_decode(scripts[brand_match.end():])[0] if brand_match else None
    images = literal(scripts, 'images')
    image_rows = images.get('default', {}).get('array', []) if isinstance(images, dict) else []
    return {'name': title.get_text(' ', strip=True), 'url': product_url(url), 'skus': rows,
            'brand': brand, 'category': crumbs[-1].get_text(' ', strip=True) if crumbs else '',
            'image': image_rows[0].get('normal') if image_rows else None}


class TaylorParser(BaseParser):
    requires_product_pages = True

    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        soup = BeautifulSoup(html, 'html.parser')
        total = soup.select_one('#__productCount')
        if total is None or not total.get_text(strip=True).isdigit():
            raise ValueError('Missing Taylor collection count')
        products = []
        for card in soup.select('#products li.product'):
            anchor = card.select_one('a[href]')
            brand = card.select_one('.info .block-with-text span')
            amount = card.select_one('.price .amount')
            if not anchor:
                raise ValueError('Taylor listing missing product link')
            products.append(Product(name=anchor.get_text(' ', strip=True), url=product_url(anchor['href']),
                                    current_price=(parse_price(amount.get_text()) or 0) if amount else 0,
                                    brand=brand.get_text(' ', strip=True) if brand else None))
        return products  # Discovery metadata only; no purchasable offers yet.

    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        soup = BeautifulSoup(html, 'html.parser')
        total_node, page_node = soup.select_one('#__productCount'), soup.select_one('input[name="pn"]')
        size_node = soup.select_one('select[name="ppg"] option[selected]')
        if not total_node or not page_node or not size_node:
            raise ValueError('Missing Taylor pagination evidence')
        total, page, size = int(total_node.get_text(strip=True)), int(page_node['value']), int(size_node['value'])
        parts = urlsplit(current_url)
        params = dict(parse_qsl(parts.query, keep_blank_values=True))
        if not 0 <= total <= 5000 or page != int(params.get('pn', '1')) or size != int(params.get('ppg', '20')):
            raise ValueError('Unexpected Taylor pagination state')
        cards = soup.select('#products li.product')
        identities = {card.get('data-product-id') for card in cards}
        # Normal pages are cumulative, including the site's explicit Show All view.
        # Distinct listing IDs can alias the same canonical product; details are deduped.
        if None in identities or len(identities) != len(cards) or len(cards) != min(page * size, total):
            raise ValueError('Incomplete or duplicate Taylor collection')
        if len(cards) == total:
            return None
        params['pn'] = str(page + 1)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params), ''))

    def parse_product_page(self, html: str, page_url: str) -> list[Product]:
        data = detail_data(html, page_url)
        offers = []
        for sku, row in data['skus'].items():
            if any(isinstance(row.get(field), bool) for field in ('price', 'regular_price', 'qty')):
                raise ValueError('Boolean Taylor price/stock')
            try:
                price, reference, stock = float(row['price']), float(row['regular_price']), float(row['qty'])
            except (ValueError, TypeError, KeyError):
                raise ValueError('Malformed Taylor price/stock') from None
            if not all(map(math.isfinite, (price, reference, stock))):
                raise ValueError('Nonfinite Taylor price/stock')
            if (not 0 < price < reference or stock <= 0 or row.get('available') is not True
                    or row.get('ib') is not False or row.get('level_name') != 'Regular'):
                continue
            url = data['url'] + ('?' + row['query'] if row['query'] else '')
            offers.append(VariantOffer(variant_key=sku + '|' + row['query'], url=url, current_price=price,
                                       original_price=reference, options=row['options'], availability='in_stock',
                                       image_url=data['image']))
        if not offers:
            return []
        best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
        return [Product(name=data['name'], url=data['url'], current_price=best.current_price,
                        original_price=best.original_price, product_type=data['category'],
                        brand=data['brand'], image_url=data['image'], offers=offers)]
