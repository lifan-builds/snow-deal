"""RA Cycles exact variants, warehouse stock and visible purchase evidence."""
import json
import math
import re
from dataclasses import replace
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup

from deal_common.parsers.common import parse_price
from deal_common.parsers.shopify import ShopifyParser, _products_json

HOST = 'racycles.com'


def _one(values, label):
    values = list(values)
    if len(values) != 1 or values[0] is None:
        raise ValueError('Missing or ambiguous RA ' + label)
    return values[0]


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate RA JSON key')
        result[key] = value
    return result


def _json(text):
    return json.loads(text, object_pairs_hook=_unique_object)


def _money(value):
    text = str(value).strip()
    if not re.fullmatch(r'\$?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?', text):
        raise ValueError('Invalid RA price')
    price = parse_price(text)
    if price is None or not math.isfinite(price) or price <= 0:
        raise ValueError('Invalid RA price')
    return price


def _minor(value, *, reference=False):
    if reference and (value is None or (type(value) is int and value == 0)):
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError('Invalid RA minor-unit price')
    return value / 100


def _visible_money(node):
    # This theme renders $2,799<sup>99</sup>; joining text loses the decimal point.
    copy = BeautifulSoup(str(node), 'html.parser')
    cents = copy.select('sup')
    if len(cents) != 1 or not re.fullmatch(r'\d{2}', cents[0].get_text(strip=True)):
        raise ValueError('Invalid RA displayed cents')
    value = cents[0].get_text(strip=True)
    cents[0].extract()
    return _money(copy.get_text('', strip=True) + '.' + value)


def _destination(url, canonical):
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    key = query.get('variant', [''])[0]
    if (parts.scheme != 'https' or parts.netloc != HOST or parts.fragment
            or parts.path != urlsplit(canonical).path or set(query) != {'variant'}
            or query['variant'] != [key] or not key.isdigit()):
        raise ValueError('Unsafe RA exact destination')
    return key


def detail_data(html: str, page_url: str, raw: dict | None = None) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    parts = urlsplit(page_url)
    if parts.scheme != 'https' or parts.netloc != HOST or not re.fullmatch(r'/products/[A-Za-z0-9_-]+', parts.path):
        raise ValueError('Unsafe RA product page')
    canonical = _one((n.get('href') for n in soup.select('link[rel="canonical"]')), 'canonical')
    if canonical != f'https://{HOST}{parts.path}':
        raise ValueError('RA canonical identity mismatch')
    main = _one(soup.select('div.product-info[id^="product-info-template-"]'), 'purchase panel')
    name = _one((n.get_text(' ', strip=True) for n in main.select('h1.product-title')), 'title')
    picker = _one(main.select('variant-picker'), 'variant picker')
    if picker.get('data-url') != parts.path:
        raise ValueError('RA picker identity mismatch')
    selected = _json(_one((n.get_text() for n in picker.select('script[type="application/json"]')), 'selected variant'))
    if not isinstance(selected, dict):
        raise TypeError('Invalid RA selected variant')
    selected_key = str(selected.get('id'))
    purchase_key = _one((n.get('value') for n in main.select('input[name="id"]')), 'purchase variant')
    if not selected_key.isdigit() or purchase_key != selected_key:
        raise ValueError('RA selected and purchase variant disagree')
    selected_options = selected.get('options')
    fields = picker.select('fieldset[data-option]')
    if (not isinstance(selected_options, list) or len(fields) != len(selected_options)
            or [n.get('data-index') for n in fields] != [str(i + 1) for i in range(len(fields))]
            or [_one((n.get('value') for n in field.select('input[checked]')), 'checked option') for field in fields] != selected_options):
        raise ValueError('RA checked options conflict with selected variant')
    requested = parse_qs(parts.query).get('variant')
    if requested is not None and requested != [selected_key]:
        raise ValueError('RA requested variant not selected')
    quantity = _one(main.select('input[name="quantity"]'), 'quantity')
    if quantity.get('value') != '1' or quantity.get('min') != '1':
        raise ValueError('Unsupported RA quantity')
    status = _json(_one((n.get_text() for n in main.select('script.variant-status-map')), 'stock map'))
    if not isinstance(status, dict) or not status:
        raise ValueError('Invalid RA stock map')
    groups = []
    for script in soup.select('script[type="application/ld+json"]'):
        value = _json(script.get_text())
        if isinstance(value, dict) and value.get('@type') == 'ProductGroup':
            groups.append(value)
    group = _one(groups, 'product group')
    product_id = str(group.get('productGroupID'))
    if not product_id.isdigit() or group.get('name') != name or group.get('url') != canonical:
        raise ValueError('RA product group identity mismatch')
    schema_variants = group.get('hasVariant')
    if not isinstance(schema_variants, list) or not schema_variants:
        raise ValueError('Missing RA complete variant schema')
    variants = {}
    for child in schema_variants:
        if not isinstance(child, dict) or child.get('@type') != 'Product' or not isinstance(child.get('offers'), dict):
            raise ValueError('Invalid RA variant schema')
        offer = child['offers']
        key = _destination(offer.get('url', ''), canonical)
        if key in variants or offer.get('priceCurrency') != 'USD' or not child.get('sku'):
            raise ValueError('Duplicate RA variant or unsupported currency/SKU')
        state = status.get(key)
        if (not isinstance(state, dict) or type(state.get('available')) is not bool
                or type(state.get('vw')) is not bool or isinstance(state.get('qty'), bool)
                or not isinstance(state.get('qty'), (int, float)) or not math.isfinite(state['qty'])):
            raise ValueError('Missing or malformed RA variant stock')
        schema_state = offer.get('availability', '').rsplit('/', 1)[-1]
        if schema_state not in {'InStock', 'OutOfStock'} or (schema_state == 'InStock') != state['available']:
            raise ValueError('Conflicting RA structured stock')
        variants[key] = {'url': offer['url'], 'sku': child['sku'], 'name': child.get('name'),
                         'price': _money(offer.get('price')), 'reference': None,
                         'available': state['available'], 'qty': state['qty'], 'virtual_warehouse': state['vw'],
                         'in_stock': state['available'] and state['qty'] > 0 and not state['vw'],
                         'options': None, 'size': None}
    if set(variants) != set(status) or selected_key not in variants:
        raise ValueError('Incomplete RA variant identity sets')
    active = [n for n in main.select('.in-stock-message') if not n.has_attr('hidden')]
    backorders = main.select('.product-backorder .backorder')
    visible_backorders = [n for n in backorders if not n.has_attr('hidden')]
    state = variants[selected_key]
    expected_class = ('in-stock-message--soldout' if not state['available'] else
                      'in-stock-message--vw' if state['virtual_warehouse'] else
                      'in-stock-message--immediate' if state['qty'] > 0 else None)
    if expected_class is None:
        if active or len(visible_backorders) != 1 or not visible_backorders[0].get_text(' ', strip=True):
            raise ValueError('RA missing selected backorder evidence')
    elif (len(active) != 1 or expected_class not in active[0].get('class', []) or visible_backorders):
        raise ValueError('RA displayed stock conflicts with selected variant')
    virtual_notice = _one(main.select('.in-stock-message--vw'), 'virtual warehouse notice').get_text(' ', strip=True)
    if not virtual_notice:
        raise ValueError('Missing RA virtual warehouse notice')
    if state['in_stock'] and active[0].get_text(' ', strip=True) != 'In Stock Ships Immediately':
        raise ValueError('RA immediate stock wording changed')
    backorder_boxes = main.select('.product-backorder .backorder .custom-backorder-message')
    backorder_note = ''
    if backorder_boxes:
        box = _one(backorder_boxes, 'backorder notice')
        # This hidden label names the currently selected size, not the shared notice.
        for title in box.select('.backorder__product'):
            title.decompose()
        backorder_note = box.get_text(' ', strip=True)
    price_node = _one(main.select('.product-info__price .price__current .js-value'), 'displayed price')
    refs = main.select('.product-info__price .price__was .js-value')
    reference = _visible_money(_one(refs, 'displayed reference')) if refs else None
    if (state['price'] != _minor(selected.get('price')) or state['price'] != _visible_money(price_node)
            or reference != _minor(selected.get('compare_at_price'), reference=True)
            or state['sku'] != selected.get('sku') or state['available'] != selected.get('available')):
        raise ValueError('RA selected identity, price or reference conflict')
    if selected.get('requires_selling_plan') is not False or selected.get('quantity_rule', {}).get('min') != 1:
        raise ValueError('Unsupported RA selling plan or minimum quantity')
    if raw is not None:
        if (not isinstance(raw, dict) or str(raw.get('id')) != product_id or raw.get('title') != name
                or '/products/' + str(raw.get('handle')) != parts.path or not isinstance(raw.get('variants'), list)):
            raise ValueError('RA product endpoint identity mismatch')
        option_defs = raw.get('options')
        if not isinstance(option_defs, list) or any(not isinstance(n, dict) or not n.get('name') for n in option_defs):
            raise ValueError('Missing RA option definitions')
        if [n['name'] for n in option_defs] != [field.get('data-option') for field in fields]:
            raise ValueError('RA option definitions conflict with visible selectors')
        size_positions = [i for i, n in enumerate(option_defs) if n['name'].casefold() in {'size', 'frame size', 'bike size'}]
        seen = set()
        for item in raw['variants']:
            key = str(item.get('id'))
            if key not in variants or key in seen:
                raise ValueError('RA product endpoint variant identity mismatch')
            seen.add(key)
            actual = variants[key]
            options = item.get('options')
            if (not isinstance(options, list) or len(options) != len(option_defs)
                    or any(not isinstance(v, str) for v in options)
                    or item.get('sku') != actual['sku'] or item.get('available') != actual['available']
                    or _minor(item.get('price')) != actual['price']
                    or item.get('requires_selling_plan') is not False
                    or item.get('quantity_rule', {}).get('min') != 1
                    or item.get('quantity_rule', {}).get('increment') != 1):
                raise ValueError('RA endpoint and purchase variant conflict')
            if actual['name'] != name + ' - ' + ' / '.join(options):
                raise ValueError('RA option identity mismatch')
            actual.update(reference=_minor(item.get('compare_at_price'), reference=True),
                          options=' / '.join(v for v in options if v != 'Default Title'),
                          size=' / '.join(options[i] for i in size_positions) or None)
        if seen != set(variants) or variants[selected_key]['reference'] != reference:
            raise ValueError('Incomplete RA endpoint variants or reference conflict')
        if selected.get('options') != raw['variants'][next(i for i, v in enumerate(raw['variants']) if str(v['id']) == selected_key)].get('options'):
            raise ValueError('RA selected options conflict')
    else:
        state.update(reference=reference, options=' / '.join(selected.get('options') or []))
    final_sale = [n.get_text(' ', strip=True) for n in main.select('.product-info__disclosure')
                  if 'final sale' in n.get_text(' ', strip=True).casefold()]
    sale_note = _one(final_sale, 'final-sale notice') if final_sale else ''
    for variant in variants.values():
        notice = virtual_notice if variant['virtual_warehouse'] else ''
        if variant['available'] and not variant['in_stock'] and not notice:
            notice = backorder_note or 'Stock not confirmed by the retailer.'
        variant['shipping_note'] = ' '.join(n for n in (notice, sale_note) if n)
    return {'url': canonical, 'name': name, 'product_id': product_id, 'currency': 'USD',
            'selected_key': selected_key, 'variants': variants, 'final_sale_note': sale_note}


class RacyclesShopifyParser(ShopifyParser):
    requires_product_pages = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products = {}
        self.variant_ids = {}
        self.product_ids = {}

    def parse_listing_page(self, html, page_url):
        products = super().parse_listing_page(html, page_url)
        raw = {item['handle']: item for item in _products_json(html) if item.get('handle')}
        for product in products:
            self.products[product.url] = product
            item = raw[urlsplit(product.url).path.rsplit('/', 1)[-1]]
            if not isinstance(item.get('variants'), list) or any(not isinstance(v, dict) for v in item['variants']):
                raise ValueError('Invalid RA feed variants')
            keys = [str(v.get('id')) for v in item['variants']]
            if len(keys) != len(set(keys)) or any(not key.isdigit() for key in keys) or not str(item.get('id')).isdigit():
                raise ValueError('Invalid RA feed identities')
            self.variant_ids[product.url] = set(keys)
            self.product_ids[product.url] = str(item['id'])
        return products

    def get_product_evidence_url(self, html, page_url):
        data = detail_data(html, page_url)
        return data['url'] + '.js?currency=USD'

    def parse_product_page(self, html, page_url):
        raise ValueError('RA exact product endpoint evidence required')

    def parse_product_evidence(self, html, page_url, evidence):
        actual = detail_data(html, page_url, _json(evidence))
        product = self.products.get(page_url)
        if (product is None or product.name != actual['name']
                or self.product_ids.get(page_url) != actual['product_id']
                or self.variant_ids.get(page_url) != set(actual['variants'])):
            raise ValueError('RA listing and detail identity mismatch')
        offers = []
        for offer in product.offers:
            row = actual['variants'].get(offer.variant_key)
            if (row is None or offer.current_price != row['price'] or offer.original_price != row['reference']
                    or offer.options != row['options'] or (offer.size and offer.size != row['size'])):
                raise ValueError('RA listing and detail offer conflict')
            if not row['available']:
                continue
            offers.append(replace(offer, availability='in_stock' if row['in_stock'] else 'unknown',
                                  availability_note=row['shipping_note']))
        if not offers:
            return []
        best = min(offers, key=lambda o: (-o.discount_pct, o.current_price, o.variant_key))
        return [replace(product, current_price=best.current_price, original_price=best.original_price,
                        image_url=best.image_url, offers=offers)]
