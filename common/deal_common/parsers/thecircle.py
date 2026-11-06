"""Circle Whistler discovery and exact Lightspeed CAD variant evidence."""
import csv
import json
import math
import re
from decimal import Decimal
from urllib.parse import parse_qsl, urlsplit

from bs4 import BeautifulSoup

from deal_common.models import Product
from deal_common.offers import VariantOffer, discount
from deal_common.parsers.base import BaseParser
from deal_common.parsers.common import parse_price

ORIGIN = 'https://www.thecirclewhistler.com'


def _one(values, label):
    values = set(values)
    if len(values) != 1:
        raise ValueError(f'Circle missing or conflicting {label}')
    return values.pop()


def _id(value):
    if isinstance(value, bool) or not re.fullmatch(r'[1-9]\d*', str(value)):
        raise ValueError('Circle invalid numeric identity')
    return str(value)


def _url(value):
    parts = urlsplit(value)
    if (parts.scheme != 'https' or parts.netloc != 'www.thecirclewhistler.com' or parts.fragment):
        raise ValueError('Circle unsafe destination')
    return parts


def product_url(value):
    parts = _url(value)
    if not re.fullmatch(r'/[a-z0-9][a-z0-9-]*\.html', parts.path):
        raise ValueError('Circle invalid product path')
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    if (len(pairs) != len(dict(pairs)) or any(key not in {'id', 'quantity'} for key, _ in pairs)
            or ('quantity' in dict(pairs) and dict(pairs)['quantity'] != '1')):
        raise ValueError('Circle invalid variant query')
    if pairs:
        _id(dict(pairs).get('id'))
    return ORIGIN + parts.path


def _amount(value):
    if isinstance(value, bool) or not re.fullmatch(r'\d+(?:\.\d+)?', str(value)):
        raise ValueError('Circle invalid money/quantity')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Circle nonfinite money/quantity')
    return result


def _cad(value, *, code=False):
    text = str(value or '').strip()
    if not re.fullmatch(r'C\$\d[\d,]*(?:\.\d{2})?' + (r' CAD' if code else ''), text):
        raise ValueError('Circle explicit CAD price required')
    result = parse_price(text)
    if result is None or not math.isfinite(result):
        raise ValueError('Circle malformed CAD price')
    return result


def _prices(raw):
    if not isinstance(raw, dict):
        raise TypeError('Circle missing exact variant price')
    values = []
    for field in ('price', 'price_old'):
        if field == 'price_old' and raw.get(field) is False:
            if (raw.get('price_old_money_with_currency') is not False
                    or any(value is not False for key, value in raw.items() if key.startswith('price_old'))):
                raise ValueError('Circle conflicting absent reference price')
            values.append(0.0)
            continue
        value = _amount(raw.get(field))
        if Decimal(str(value)) != Decimal(str(_cad(raw.get(field + '_money_with_currency'), code=True))):
            raise ValueError('Circle numeric/formatted price conflict')
        values.append(value)
    if values[0] <= 0:
        raise ValueError('Circle nonpositive price')
    return tuple(values)


def _display_prices(node):
    copy = BeautifulSoup(str(node), 'html.parser')
    old = copy.select('.slashed')
    if len(old) > 1:
        raise ValueError('Circle ambiguous reference price')
    reference = _cad(old[0].get_text(strip=True)) if old else 0
    for child in old:
        child.decompose()
    return _cad(copy.get_text(' ', strip=True)), reference


def _option(label):
    key, separator, value = str(label).partition(':')
    if not separator or not key.strip() or not value.strip():
        raise ValueError('Circle missing option label/value')
    return key.strip().casefold(), value.strip()


def _options(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Circle missing variant options')
    quoted = value.lstrip().startswith('"')
    if quoted and not re.fullmatch(r'"(?:[^"]|"")*"(?:, *(?:"(?:[^"]|"")*"|[^",\r\n]*))*', value.strip()):
        # csv strict mode still accepts bare quotes inside unquoted fields.
        raise ValueError('Circle malformed variant options')
    try:
        # The endpoint embeds CSV inside JSON; doubled quotes are literal inches.
        labels = (next(csv.reader([value.strip()], strict=True, skipinitialspace=True))
                  if quoted else [value])
    except csv.Error as exc:
        raise ValueError('Circle malformed variant options') from exc
    if not isinstance(labels, list) or not labels or any(not isinstance(v, str) for v in labels):
        raise ValueError('Circle malformed variant options')
    pairs = [_option(label) for label in labels]
    if len(dict(pairs)) != len(pairs):
        raise ValueError('Circle duplicate option dimensions')
    return dict(pairs)


def _child_age_size(value):
    if not isinstance(value, str):
        return False
    text = value.strip().casefold()
    wrapped = re.fullmatch(r'(?:[1-9][0-9]{1,2}(?:/[1-9][0-9]{1,2})?|xs|s|m|l|xl)\s*\(([^()]+)\)', text)
    if wrapped:
        text = wrapped[1]
    age = re.fullmatch(r'([0-9]{1,2}(?:\.[0-9])?)(?:\s*[-–]\s*([0-9]{1,2}(?:\.[0-9])?))?\s*(yr?|mo?|t)', text)
    if not age:
        return False
    lower, upper = Decimal(age[1]), Decimal(age[2] or age[1])
    limit = {'y': 16, 'm': 24, 't': 10}[age[3][0]]
    return 0 <= lower <= upper <= limit and upper > 0 and (age[3] != 't' or lower >= 1)


def _children_sizing(raw, sizes):
    """Record containment evidence without declaring every sibling a child size."""
    marker = 'Includes children sizing'
    if any(_child_age_size(size) for size in sizes):
        return marker
    brand = raw.get('brand')
    if (isinstance(brand, dict) and str(brand.get('id')) == '2212719' and brand.get('title') == 'Miles'
            and brand.get('url') == ORIGIN + '/brands/miles/'
            and any(isinstance(size, str) and re.fullmatch(r'[2-9]|1[0-4]', size) for size in sizes)):
        return marker
    description = raw.get('description')
    if isinstance(description, str):
        text = BeautifulSoup(description, 'html.parser').get_text(' ', strip=True)
        age = re.search(r'\bages\s+([0-9]{1,2}(?:\.[0-9])?(?:\s*[-–]\s*[0-9]{1,2}(?:\.[0-9])?)?)'
                        r'\s+years,\s+for a child\b', text, re.IGNORECASE)
        if age and _child_age_size(age[1] + 'Y'):
            return marker
    return None


def _stock(raw):
    if not isinstance(raw, dict):
        raise TypeError('Circle missing stock object')
    available, on_stock, tracked = (raw.get(k) for k in ('available', 'on_stock', 'track'))
    if any(v is not None and not isinstance(v, bool) for v in (available, on_stock, tracked)):
        raise ValueError('Circle malformed stock flags')
    level = _amount(raw['level']) if raw.get('level') is not None else None
    backorder_flags = [raw[key] for key in ('allow_backorders', 'allow_outofstock_sale') if raw.get(key) is not None]
    if any(not isinstance(value, bool) for value in backorder_flags):
        raise ValueError('Circle malformed backorder flag')
    if len(set(backorder_flags)) > 1:
        raise ValueError('Circle conflicting backorder flags')
    backorders = raw.get('allow_backorders', raw.get('allow_outofstock_sale'))
    delivery = raw.get('delivery')
    delayed = delivery is not False and delivery is not None
    if (available is False and on_stock is True
            or (available is True and on_stock is False and backorders is False and not delayed)
            or (tracked is True and on_stock is True and level == 0)):
        raise ValueError('Circle conflicting stock evidence')
    if available is False:
        state, note = 'out_of_stock', ''
    elif backorders is True:
        state, note = 'unknown', 'Retailer permits backorders; stock needs confirmation.'
    elif delayed:
        detail = delivery.strip() if isinstance(delivery, str) else ''
        state, note = 'unknown', 'Retailer delivery notice: ' + (detail[:160] or 'Timing needs confirmation.')
    elif (available is True and on_stock is True and tracked is True and level is not None and level > 0
          and backorders is False and delivery is False):
        state, note = 'in_stock', ''
    else:
        state, note = 'unknown', 'Retailer stock evidence is incomplete.'
    return {'availability': state, 'availability_note': note,
            'identity': (available, on_stock, tracked, level, backorders, delivery)}


def _image_id(value):
    parts = urlsplit(value)
    match = re.fullmatch(r'/shops/628048/files/([1-9]\d*)/[^/]+/[^/]+', parts.path)
    if (parts.scheme != 'https' or parts.netloc != 'cdn.shoplightspeed.com' or not match
            or parts.query or parts.fragment):
        raise ValueError('Circle unsafe or unbound image')
    return match[1]


def _html_data(html, url):
    family = product_url(url)
    soup = BeautifulSoup(html, 'html.parser')
    canonical = _one((n.get('href') for n in soup.select('link[rel="canonical"]')), 'canonical')
    if canonical != family:
        raise ValueError('Circle canonical family mismatch')
    info = soup.select('.product-info[itemprop="offers"]')
    forms = soup.select('#product_configure_form')
    if len(info) != 1 or len(forms) != 1:
        raise ValueError('Circle missing main purchase panel')
    info, form = info[0], forms[0]
    action = _url(form.get('action', ''))
    match = re.fullmatch(r'/cart/add/([1-9]\d*)/', action.path)
    if not match or action.query:
        raise ValueError('Circle missing selected variant action')
    selected = match[1]
    requested = dict(parse_qsl(urlsplit(url).query)).get('id')
    if requested and requested != selected:
        raise ValueError('Circle requested variant was substituted')
    quantities = form.select('input[name="quantity"]')
    quantity_id = re.fullmatch(r'qty_([1-9]\d*)', quantities[0].get('id', '')) if len(quantities) == 1 else None
    if not quantity_id:
        raise ValueError('Circle missing or ambiguous quantity product identity')
    pid = quantity_id[1]
    buttons = form.select('[data-pid], [data-vid]')
    if buttons:
        if (len(buttons) != 1 or buttons[0].name != 'button' or len(form.select('button')) != 1
                or buttons[0].has_attr('disabled') or buttons[0].get('aria-disabled', '').casefold() == 'true'
                or 'out' in buttons[0].get('class', [])
                or buttons[0].get_text(' ', strip=True) != 'Add to Cart'):
            raise ValueError('Circle conflicting or ambiguous purchase control')
        if _one((_id(n.get('data-pid')) for n in buttons), 'button product identity') != pid:
            raise ValueError('Circle quantity/button product conflict')
        if _one((_id(n.get('data-vid')) for n in buttons), 'selected button variant') != selected:
            raise ValueError('Circle selected form/button conflict')
    name = _one((n.get_text(' ', strip=True) for n in info.select('h1.product__title')), 'title')
    if not name:
        raise ValueError('Circle missing product title')
    currency = _one((n.get('content') for n in info.select('meta[itemprop="priceCurrency"]')), 'currency')
    if currency != 'CAD':
        raise ValueError('Circle non-CAD product panel')
    condition = _one((n.get('content') for n in info.select('meta[itemprop="itemCondition"]')), 'condition')
    availability = _one((n.get('content') for n in info.select('meta[itemprop="availability"]')), 'availability')
    if condition not in {'http://schema.org/NewCondition', 'https://schema.org/NewCondition'}:
        raise ValueError('Circle product is not explicitly new')
    if not buttons:
        controls = form.select('button.out')
        if (availability not in {'http://schema.org/OutOfStock', 'https://schema.org/OutOfStock'}
                or len(controls) != 1 or len(form.select('button')) != 1
                or controls[0].get_text(' ', strip=True) != 'Out of Stock'):
            raise ValueError('Circle missing explicit selected sold-out control')
    prices = info.select('.price[data-reg-price]')
    if len(prices) != 1:
        raise ValueError('Circle missing visible selected price')
    money = _display_prices(prices[0])
    if (_cad(prices[0].get('data-reg-price')) != money[0]
            or _cad(prices[0].get('data-old-price')) != money[1]
            or _one((_amount(n.get('content')) for n in info.select('meta[itemprop="price"]')), 'structured price') != money[0]):
        raise ValueError('Circle displayed/structured price conflict')
    selection = {}
    size_values = []
    native = form.select('select[name="variant"]')
    default_selection = bool(native)
    if native:
        options = native[0].select('option')
        if (len(native) != 1 or len(form.select('select')) != 1 or len(options) != 1
                or not options[0].has_attr('selected') or _id(options[0].get('value')) != selected):
            raise ValueError('Circle ambiguous default native selection')
        label = options[0].get_text(' ', strip=True)
        if not label.startswith('Default - ') or _cad(label.removeprefix('Default - ')) != money[0]:
            raise ValueError('Circle default native price/label conflict')
    for select in form.select('select[name^="matrix["]'):
        key = re.fullmatch(r'matrix\[([^\]]+)\]', select.get('name', ''))
        values = [n.get('value') for n in select.select('option[selected]')]
        if not key or len(values) != 1 or not values[0] or key[1].casefold() in selection:
            raise ValueError('Circle ambiguous selected dimensions')
        selection[key[1].casefold()] = values[0]
        if key[1].casefold() == 'size':
            size_values = [n.get('value') for n in select.select('option')]
    variants = {}
    nodes = soup.select('.product_variants [data-vid]')
    if default_selection and len(nodes) != 1:
        raise ValueError('Circle ambiguous default DOM variants')
    for node in nodes:
        key = _id(node.get('data-vid'))
        if key in variants or node.get('data-availability') not in {'', '1'}:
            raise ValueError('Circle duplicate/malformed variant DOM')
        labels = {name: value for name, value in node.attrs.items()
                  if name.startswith('data-') and name not in {'data-vid', 'data-image', 'data-availability'}}
        if default_selection:
            if key != selected or labels != {'data-color': 'Default', 'data-size': 'Default'}:
                raise ValueError('Circle default DOM label/identity conflict')
            options = {}
        else:
            options = dict(_option(value) for value in labels.values())
        variants[key] = {'options': options, 'available': node['data-availability'] == '1',
                         'image': _id(node['data-image']) if node.get('data-image') else None}
    images = {_image_id(n['src']): n['src'] for n in soup.select('#prod_slider img[src]')}
    return {'url': family, 'id': pid, 'selected': selected, 'name': name, 'money': money,
            'selection': selection, 'size_values': size_values, 'variants': variants, 'images': images,
            'default_selection': default_selection, 'has_purchase_button': bool(buttons),
            'available': availability.rsplit('/', 1)[-1]}


def _json(value):
    def unique(pairs):
        if len(dict(pairs)) != len(pairs):
            raise ValueError('Circle duplicate JSON keys')
        return dict(pairs)
    return json.loads(value, object_pairs_hook=unique)


def detail_data(html, page_url, evidence):
    """Bind two separately fetched public payloads; never evaluate theme scripts."""
    actual = _html_data(html, page_url)
    raw = _json(evidence)
    if (not isinstance(raw, dict) or _id(raw.get('id')) != actual['id']
            or raw.get('url') != actual['url'] or raw.get('title', '').strip() != actual['name']
            or _id(raw.get('vid')) != actual['selected']):
        raise ValueError('Circle HTML/endpoint identity conflict')
    variants = raw.get('variants')
    if not isinstance(variants, dict) or not variants or set(variants) != set(actual['variants']):
        raise ValueError('Circle incomplete or conflicting variant set')
    if actual['default_selection'] and (len(variants) != 1 or raw.get('variant') != ''):
        raise ValueError('Circle conflicting default endpoint selection')
    image_urls = raw.get('images')
    if not isinstance(image_urls, list):
        raise TypeError('Circle missing image evidence')
    endpoint_images = {_image_id(value): value for value in image_urls}
    images = {**endpoint_images, **actual['images']}
    rows = {}
    inch_comparison = False
    for key, variant in variants.items():
        if not isinstance(variant, dict) or _id(key) != _id(variant.get('id')):
            raise ValueError('Circle variant identity conflict')
        destination = variant.get('url', '')
        if product_url(destination) != actual['url'] or dict(parse_qsl(urlsplit(destination).query)).get('id') != key:
            raise ValueError('Circle variant destination mismatch')
        if actual['default_selection']:
            if variant.get('title') != 'Default' or variant.get('default') is not True:
                raise ValueError('Circle conflicting default variant label/flag')
            options = {}
        else:
            options = _options(variant.get('title'))
        dom = actual['variants'][key]
        image_id = _id(variant['image']) if variant.get('image') else None
        stock = _stock(variant.get('stock'))
        if options != dom['options']:
            size = options.get('size', '')
            if (not re.fullmatch(r'[1-9][0-9]*"', size)
                    or {**options, 'size': size[:-1]} != dom['options']
                    or actual['size_values'].count(size) != 1
                    or size[:-1] in actual['size_values']):
                raise ValueError('Circle variant DOM/endpoint conflict')
            # Native navigation proves this exact numeric-inch omission only.
            inch_comparison = True
        if (dom['image'] != image_id
                or (isinstance(variant['stock'].get('available'), bool)
                    and dom['available'] != variant['stock']['available'])):
            raise ValueError('Circle variant DOM/endpoint conflict')
        if image_id and image_id not in images:
            raise ValueError('Circle variant image absent')
        price, reference = _prices(variant.get('price'))
        rows[key] = {'url': destination, 'price': price, 'reference': reference, 'options': options,
                     'size': options.get('size') or options.get('length'), 'image': images.get(image_id),
                     'sku': variant.get('sku'), **stock}
    if inch_comparison:
        comparisons = [tuple(sorted((key, value[:-1] if key == 'size' and re.fullmatch(r'[1-9][0-9]*"', value)
                                     else value) for key, value in row['options'].items())) for row in rows.values()]
        if len(set(comparisons)) != len(rows):
            raise ValueError('Circle ambiguous inch-size variants')
    selected = rows[actual['selected']]
    api_selection = {} if actual['default_selection'] else _options(raw.get('variant'))
    if (selected['options'] != actual['selection'] or api_selection != selected['options']
            or _prices(raw.get('price')) != actual['money']
            or (selected['price'], selected['reference']) != actual['money']
            or raw.get('sku') != selected['sku']
            or _stock(raw.get('stock'))['identity'] != selected['identity']):
        raise ValueError('Circle selected variant evidence conflict')
    if not actual['has_purchase_button'] and selected['identity'] != (False, False, True, 0, False, False):
        raise ValueError('Circle missing independent selected sold-out evidence')
    selected_image = variants[actual['selected']].get('image')
    if selected_image is not None:
        if (raw.get('image_id') != selected_image
                or (selected_image and _image_id(raw.get('image', '')) != str(selected_image))):
            raise ValueError('Circle selected image conflict')
    elif raw.get('image_id') is not None:
        fallback_image = _id(raw['image_id'])
        if (fallback_image not in endpoint_images or fallback_image not in actual['images']
                or _image_id(raw.get('image', '')) != fallback_image):
            raise ValueError('Circle unbound product gallery image')
    if ((selected['availability'] == 'in_stock' and actual['available'] != 'InStock')
            or (selected['availability'] == 'out_of_stock' and actual['available'] == 'InStock')):
        raise ValueError('Circle selected stock conflict')
    return {**actual, 'variants': rows, 'brand': (raw.get('brand') or {}).get('title'),
            'product_type': _children_sizing(raw, [row['size'] for row in rows.values()])}


class TheCircleParser(BaseParser):
    requires_product_pages = True

    def __init__(self):
        self.collections = {}
        self.product_ids = {}
        self.product_urls = {}

    def _listing(self, html, url):
        parts = _url(url)
        match = re.fullmatch(r'/(sale|snow)/(?:page([1-9]\d*)\.html)?', parts.path)
        if not match or parts.query:
            raise ValueError('Circle unsupported collection URL')
        page = int(match[2] or 1)
        base = ORIGIN + '/' + match[1] + '/'
        soup = BeautifulSoup(html, 'html.parser')
        canonical = _one((n.get('href') for n in soup.select('link[rel="canonical"]')), 'collection canonical')
        cards = soup.select('#ls-product-results .prod-card')
        if canonical not in {base, url} or not cards or len(cards) > 24:
            raise ValueError('Circle missing/malformed collection')
        pagers = soup.select('ul.pager[aria-label="Pagination"]')
        if not pagers:
            if page != 1 or len(cards) == 24:
                raise ValueError('Circle missing pagination')
            return cards, base, page, 1, None
        if len(pagers) != 1:
            raise ValueError('Circle ambiguous pagination')
        pager = pagers[0]
        active = pager.select('li[aria-current="true"] a')
        if len(active) != 1 or active[0].get_text(strip=True) != str(page):
            raise ValueError('Circle requested/active page conflict')
        numbers = []
        for anchor in pager.select('li a'):
            label = anchor.get_text(strip=True)
            if label.isdigit():
                number = int(label)
                expected = base if number == 1 else base + f'page{number}.html'
                if anchor.get('href') != expected:
                    raise ValueError('Circle unsafe or inconsistent page link')
                numbers.append(number)
        total = max(numbers, default=0)
        next_links = pager.select('li.enabled.next a')
        forward = pager.select('li:has(.arrow-right)')
        expected_next = base + f'page{page + 1}.html'
        if (total < page or len(set(numbers)) != len(numbers)
                or len(forward) != 1
                or (page < total and (len(cards) != 24 or len(next_links) != 1
                                     or next_links[0].get('href') != expected_next
                                     or forward[0].get('aria-disabled') == 'true'))
                or (page == total and (next_links or forward[0].get('aria-disabled') != 'true'
                                      or 'disabled' not in forward[0].get('class', [])))):
            raise ValueError('Circle incomplete pagination state')
        return cards, base, page, total, expected_next if page < total else None

    def parse_listing_page(self, html, page_url):
        cards, base, page, total, _ = self._listing(html, page_url)
        previous = self.collections.get(base)
        if page != 1 and (not previous or previous['page'] != page - 1 or previous['terminal_page'] != total):
            raise ValueError('Circle missing/repeated page or changed terminal page')
        seen = set(previous['ids']) if page != 1 else set()
        products, identities = [], {}
        for card in cards:
            pid = _id(card.get('data-product-id'))
            anchor, price = card.select_one('.title a'), card.select_one('.price')
            url = product_url(card.get('data-url', ''))
            if (pid in seen or url in identities or not anchor or anchor.get('href') != url or card.get('data-url') != url
                    or not price or self.product_ids.get(url, pid) != pid or self.product_urls.get(pid, url) != url):
                raise ValueError('Circle repeated or conflicting discovery identity')
            seen.add(pid)
            current, reference = _display_prices(price)
            identities[url] = pid
            if discount(current, reference) <= 0:
                continue
            brand, image = card.select_one('.product_brand'), card.select_one('img[src]')
            products.append(Product(anchor.get_text(' ', strip=True), url, current, reference,
                                    brand=brand.get_text(' ', strip=True) if brand else None,
                                    image_url=image.get('src') if image else None))
        self.product_ids.update(identities)
        self.product_urls.update({pid: url for url, pid in identities.items()})
        self.collections[base] = {'page': page, 'terminal_page': total, 'ids': seen}
        return products

    def get_next_page_url(self, html, current_url):
        return self._listing(html, current_url)[-1]

    def get_product_evidence_url(self, html, page_url):
        actual = _html_data(html, page_url)
        query = urlsplit(page_url).query
        return actual['url'][:-5] + '.ajax' + ('?' + query if query else '')

    def parse_product_page(self, html, page_url):
        raise ValueError('Circle separate exact product endpoint evidence required')

    def parse_product_evidence(self, html, page_url, evidence):
        actual = detail_data(html, page_url, evidence)
        if self.product_ids.get(actual['url'], actual['id']) != actual['id']:
            raise ValueError('Circle discovery/detail product identity conflict')
        offers = [VariantOffer(key, row['url'], row['price'], row['reference'], size=row['size'],
                               options=' / '.join(f'{k.title()}: {v}' for k, v in row['options'].items()),
                               availability=row['availability'], availability_note=row['availability_note'],
                               image_url=row['image']) for key, row in actual['variants'].items()
                  if row['availability'] != 'out_of_stock' and discount(row['price'], row['reference']) > 0]
        if not offers:
            return []
        best = min(offers, key=lambda o: (-o.discount_pct, -(o.original_price - o.current_price),
                                         o.current_price, o.variant_key))
        return [Product(actual['name'], actual['url'], best.current_price, best.original_price,
                        sizes=list(dict.fromkeys(o.size for o in offers if o.size)) or None,
                        product_type=actual['product_type'], brand=actual['brand'], image_url=best.image_url, offers=offers)]
