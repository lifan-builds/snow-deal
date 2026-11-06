"""Reduced public Circle captures plus labeled synthetic conflict controls."""
import asyncio
import json
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup
from deal_common.catalog.query import query
from deal_common.config import RetailerConfig
from deal_common.http import fetch_products
from deal_common.parsers.thecircle import ORIGIN, TheCircleParser, detail_data

FIXTURES = Path(__file__).parent / 'fixtures/thecircle'
URL = ORIGIN + '/jackson-mips-helmet.html'
KEY = '100724076'
OTHER = '100724075'


def capture(stem='jackson'):
    return (FIXTURES / (stem + '.html')).read_text(), json.loads((FIXTURES / (stem + '.json')).read_text())


def parse(html, raw, url=URL):
    return TheCircleParser().parse_product_evidence(html, url, json.dumps(raw))


@pytest.mark.parametrize('row', json.loads((FIXTURES / 'manifest.json').read_text()), ids=lambda r: r['stem'])
def test_all_captured_shapes_reconcile_complete_variants_and_available_exact_offers(row):
    html, raw = capture(row['stem'])
    original = deepcopy(raw)
    actual = detail_data(html, row['url'], json.dumps(raw))
    assert len(actual['variants']) == row['variant_count']
    product = parse(html, raw, row['url'])[0]
    expected = {key: v for key, v in raw['variants'].items() if v['stock']['available']}
    assert {o.variant_key for o in product.offers} == set(expected)
    assert product.name == raw['title'] and product.brand == raw['brand']['title']
    assert product.url == row['url']
    for offer in product.offers:
        source = expected[offer.variant_key]
        assert (offer.current_price, offer.original_price, offer.url) == (
            source['price']['price'], source['price']['price_old'], source['url'])
        assert offer.availability == 'in_stock' and not offer.availability_note
        if source['image']:
            assert '/files/' + str(source['image']) + '/' in offer.image_url
        else:
            assert offer.image_url is None  # Unknown variant image is not borrowed.
    if row['stem'] == 'shapes-03':
        assert product.offers[0].size is None  # Color-only singleton is not a size.
    if row['stem'] == 'shapes-01':
        assert product.offers[0].size == '160W'  # Unquoted Size : value.
    assert raw == original


def test_jackson_has_exact_xl_offer_image_and_no_unavailable_l_offer():
    html, raw = capture()
    parser = TheCircleParser()
    assert parser.get_product_evidence_url(html, URL) == URL[:-5] + '.ajax'
    assert parser.get_product_evidence_url(html, URL + '?id=' + KEY + '&quantity=1') == (
        URL[:-5] + '.ajax?id=' + KEY + '&quantity=1')
    p = parse(html, raw)[0]
    o = p.offers[0]
    assert (o.variant_key, o.size, o.options, o.current_price, o.original_price, o.url) == (
        KEY, 'XL', 'Color: Matte Black / Size: XL', 81, 269.99, URL + '?id=' + KEY)
    assert '790x680x2' in o.image_url
    with pytest.raises(ValueError, match='substituted'):
        parse(html, raw, URL + '?id=' + OTHER)
    with pytest.raises(ValueError, match='endpoint evidence required'):
        parser.parse_product_page(html, URL)


def test_synthetic_siblings_keep_distinct_money_options_images_and_destinations():
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    row = raw['variants'][OTHER]
    row['price'].update(price=120, price_old=300, price_money_with_currency='C$120.00 CAD',
                        price_old_money_with_currency='C$300.00 CAD')
    row['stock'].update(available=True, on_stock=True, level=1)
    row['image'] = 59676655
    node = soup.select_one('.product_variants [data-vid="' + OTHER + '"]')
    node['data-availability'], node['data-image'] = '1', '59676655'
    offers = {o.variant_key: o for o in parse(str(soup), raw)[0].offers}
    assert (offers[OTHER].current_price, offers[OTHER].original_price, offers[OTHER].size) == (120, 300, 'L')
    assert offers[OTHER].url == URL + '?id=' + OTHER
    assert '/59676655/' in offers[OTHER].image_url
    assert offers[KEY].current_price == 81 and '/59676659/' in offers[KEY].image_url


@pytest.mark.parametrize('change', ['id', 'title', 'url', 'vid', 'variant_set', 'extra_variant', 'variant_id',
                                  'variant_url', 'variant_options', 'variant_image', 'selected_image', 'selected_sku'])
def test_conflicting_endpoint_identity_variant_options_or_image_fails(change):
    html, raw = capture()
    if change in {'id', 'vid'}:
        raw[change] = 999
    elif change in {'title', 'url'}:
        raw[change] = 'Different product'
    elif change == 'variant_set':
        raw['variants'].pop(OTHER)
    elif change == 'extra_variant':
        raw['variants']['999'] = deepcopy(raw['variants'][OTHER])
    elif change == 'variant_id':
        raw['variants'][OTHER]['id'] = 999
    elif change == 'variant_url':
        raw['variants'][OTHER]['url'] = URL + '?id=' + KEY
    elif change == 'variant_options':
        raw['variants'][OTHER]['title'] = 'Size: XXL'
    elif change == 'variant_image':
        raw['variants'][OTHER]['image'] = 59676655
    elif change == 'selected_image':
        raw['image_id'] = 59676655
    else:
        raw['sku'] = 'DIFFERENT-SKU'
    with pytest.raises((ValueError, TypeError)):
        parse(html, raw)


@pytest.mark.parametrize('change', ['canonical', 'heading', 'product_id', 'button_variant', 'selected_size',
                                  'currency', 'reference', 'availability', 'condition', 'duplicate_dom'])
def test_conflicting_html_purchase_panel_fails(change):
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    if change == 'canonical':
        soup.select_one('link[rel="canonical"]')['href'] = ORIGIN + '/different.html'
    elif change == 'heading':
        soup.select_one('h1').string = 'Wrong model'
    elif change in {'product_id', 'button_variant'}:
        soup.select_one('button')['data-pid' if change == 'product_id' else 'data-vid'] = '999'
    elif change == 'selected_size':
        soup.select_one('select[name="matrix[size]"] option[selected]')['value'] = 'L'
    elif change == 'currency':
        soup.select_one('meta[itemprop="priceCurrency"]')['content'] = 'USD'
    elif change == 'reference':
        soup.select_one('.price')['data-old-price'] = 'C$199.99'
    elif change == 'availability':
        soup.select_one('meta[itemprop="availability"]')['content'] = 'https://schema.org/OutOfStock'
    elif change == 'condition':
        soup.select_one('meta[itemprop="itemCondition"]')['content'] = 'https://schema.org/UsedCondition'
    else:
        soup.select_one('.product_variants').append(deepcopy(soup.select_one('.product_variants [data-vid]')))
    with pytest.raises((ValueError, TypeError)):
        parse(str(soup), raw)


@pytest.mark.parametrize('value', [True, False, None, 'NaN', 'Infinity', -1, 'unknown'])
def test_invalid_exact_variant_money_cannot_fall_back_to_product_default(value):
    html, raw = capture()
    raw['variants'][OTHER]['price']['price'] = value
    with pytest.raises(ValueError):
        parse(html, raw)


@pytest.mark.parametrize('change', ['formatted_amount', 'formatted_currency', 'missing_price', 'json_duplicate'])
def test_price_currency_and_json_integrity_is_required_even_for_unavailable_siblings(change):
    html, raw = capture()
    if change == 'json_duplicate':
        with pytest.raises(ValueError, match='duplicate JSON'):
            detail_data(html, URL, '{"id":1,"id":2}')
        return
    row = raw['variants'][OTHER]
    if change == 'formatted_amount':
        row['price']['price_money_with_currency'] = 'C$80.00 CAD'
    elif change == 'formatted_currency':
        row['price']['price_money_with_currency'] = '$81.00 USD'
    else:
        row.pop('price')
    with pytest.raises((ValueError, TypeError)):
        parse(html, raw)


@pytest.mark.parametrize('change', [{'track': False}, {'level': None}, {'allow_backorders': True},
                                  {'delivery': 'Ships in 2 weeks'}])
def test_synthetic_incomplete_backorder_and_delivery_evidence_remain_unknown_and_not_exact_stock(change):
    html, raw = capture()
    raw['variants'][KEY]['stock'].update(change)
    raw['stock'].update({('allow_outofstock_sale' if k == 'allow_backorders' else k): v for k, v in change.items()})
    product = parse(html, raw)[0]
    offer = product.offers[0]
    assert offer.availability == 'unknown' and offer.availability_note
    normalized = {'name': product.name, 'url': product.url, 'brand': product.brand,
                  'category': 'Helmets', 'format': '', 'platform': '', 'offers': [asdict(offer)]}
    sources = [{'name': 'Circle', 'successful_at': datetime.now(UTC).isoformat(), 'products': [normalized]}]
    filters = {'min_reference': 0, 'min_discount': 0, 'max_price': 0, 'page': 1}
    assert query(sources, filters)['total'] == 1
    assert query(sources, {**filters, 'size': 'XL'})['total'] == 0
    assert query(sources, {**filters, 'stock': True})['total'] == 0


@pytest.mark.parametrize('value', [True, 'NaN', -1])
def test_malformed_or_contradictory_quantity_fails(value):
    html, raw = capture()
    raw['variants'][KEY]['stock']['level'] = value
    with pytest.raises(ValueError):
        parse(html, raw)


def test_synthetic_consistent_sold_out_family_has_no_purchasable_offers():
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    raw['variants'][KEY]['stock'].update(available=False, on_stock=False, level=0)
    raw['stock'].update(available=False, on_stock=False, level=0)
    soup.select_one('.product_variants [data-vid="' + KEY + '"]')['data-availability'] = ''
    soup.select_one('meta[itemprop="availability"]')['content'] = 'http://schema.org/OutOfStock'
    assert parse(str(soup), raw) == []


@pytest.mark.parametrize('url', ['https://evil.example/jackson-mips-helmet.html',
                               URL + '?id=' + KEY + '&id=' + KEY, URL + '?id=' + KEY + '&redirect=evil',
                               URL + '?id=' + KEY + '#other', URL + '?quantity=1'])
def test_unsafe_and_ambiguous_exact_product_destinations_fail(url):
    html, raw = capture()
    with pytest.raises(ValueError):
        parse(html, raw, url)


def listing(collection='sale', page=1, *, total=18, new_ids=False):
    soup = BeautifulSoup((FIXTURES / f'{collection}-1.html').read_text(), 'html.parser')
    base = ORIGIN + '/' + collection + '/'
    soup.select_one('li[aria-current="true"] a').string = str(page)
    soup.select_one('li[aria-current="true"] a')['href'] = base if page == 1 else base + f'page{page}.html'
    pager = soup.select_one('.pager')
    for li in list(pager.select('li')):
        if li.has_attr('aria-current') or 'next' in li.get('class', []) or li.get('aria-disabled') == 'true':
            continue
        li.decompose()
    terminal = soup.new_tag('li')
    anchor = soup.new_tag('a', href=base + f'page{total}.html')
    anchor.string = str(total)
    terminal.append(anchor)
    pager.insert(-1, terminal)
    pager.select_one('li.next a')['href'] = base + f'page{page+1}.html'
    if new_ids:
        for index, card in enumerate(soup.select('.prod-card')):
            card['data-product-id'] = str(900000000 + index)
            card['data-url'] = ORIGIN + f'/synthetic-{index}.html'
            card.select_one('.title a')['href'] = card['data-url']
    return str(soup)


def test_captured_pages_require_full_traversal_and_explicit_terminal_state():
    for collection, discounted in [('sale', 24), ('snow', 0)]:
        parser = TheCircleParser()
        first = (FIXTURES / f'{collection}-1.html').read_text()
        base = ORIGIN + '/' + collection + '/'
        assert len(parser.parse_listing_page(first, base)) == discounted
        assert parser.get_next_page_url(first, base) == base + 'page2.html'
        assert parser.get_next_page_url((FIXTURES / f'{collection}-18.html').read_text(), base + 'page18.html') is None
        assert len(parser.collections[base]['ids']) == 24


@pytest.mark.parametrize('change', ['active', 'skip', 'unsafe', 'missing_pager', 'missing_card', 'duplicate_id',
                                  'missing_id', 'duplicate_url', 'wrong_currency', 'challenge'])
def test_malformed_discovery_and_pagination_cannot_report_success(change):
    soup = BeautifulSoup(listing(), 'html.parser')
    if change == 'active':
        soup.select_one('li[aria-current] a').string = '2'
    elif change in {'skip', 'unsafe'}:
        soup.select_one('li.next a')['href'] = ORIGIN + '/sale/page3.html' if change == 'skip' else 'https://evil.example/'
    elif change == 'missing_pager':
        soup.select_one('.pager').decompose()
        # Missing the pager on an already-started second page is not terminal.
        with pytest.raises(ValueError):
            TheCircleParser().get_next_page_url(str(soup), ORIGIN + '/sale/page2.html')
        return
    elif change == 'missing_card':
        soup.select_one('.prod-card').decompose()
    elif change == 'duplicate_id':
        soup.select('.prod-card')[1]['data-product-id'] = soup.select_one('.prod-card')['data-product-id']
    elif change == 'missing_id':
        del soup.select_one('.prod-card')['data-product-id']
    elif change == 'duplicate_url':
        card = soup.select('.prod-card')[1]
        card['data-url'] = soup.select_one('.prod-card')['data-url']
        card.select_one('.title a')['href'] = card['data-url']
    elif change == 'wrong_currency':
        soup.select_one('.price').string = '$10.00 USD'
    else:
        soup = BeautifulSoup('<html>Challenge</html>', 'html.parser')
    with pytest.raises(ValueError):
        TheCircleParser().parse_listing_page(str(soup), ORIGIN + '/sale/')


def test_repeated_ids_changed_terminal_and_missing_middle_page_fail():
    for second, url in [(listing(page=2), ORIGIN + '/sale/page2.html'),
                        (listing(page=2, total=19, new_ids=True), ORIGIN + '/sale/page2.html'),
                        (listing(page=3, new_ids=True), ORIGIN + '/sale/page3.html')]:
        parser = TheCircleParser()
        parser.parse_listing_page(listing(), ORIGIN + '/sale/')
        with pytest.raises(ValueError):
            parser.parse_listing_page(second, url)


def single_listing(collection='sale', *, full_price=False):
    _, raw = capture()
    return (f'<link rel="canonical" href="{ORIGIN}/{collection}/"><div id="ls-product-results">'
            f'<div class="prod-card" data-product-id="{raw["id"]}" data-url="{URL}">'
            f'<div class="title"><a href="{URL}">{raw["title"]}</a></div>'
            '<div class="product_brand">Giro</div><div class="price">'
            + ('' if full_price else '<span class="slashed">C$269.99</span>')
            + 'C$81.00</div></div></div>')


def test_singleton_full_price_and_cross_collection_aliases_use_existing_evidence_hook():
    html, raw = capture()
    requested = []
    def handler(request):
        requested.append(str(request.url))
        if request.url.path.endswith('.ajax'):
            return httpx.Response(200, json=raw)
        if request.url.path.endswith('.html'):
            return httpx.Response(200, text=html)
        listing_html = single_listing(request.url.path.strip('/'))
        if request.url.path == '/snow/':
            listing_html = listing_html.replace(raw['title'], 'Collection-specific display alias')
        return httpx.Response(200, text=listing_html)
    async def run():
        outcome = {'errors': 0, 'pages': 0}
        store = RetailerConfig('Circle', 'www.thecirclewhistler.com', [ORIGIN + '/sale/', ORIGIN + '/snow/'],
                               parser_type='thecircle', currency='CAD')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            products = await fetch_products(store, TheCircleParser(), client, semaphore=asyncio.Semaphore(1),
                                            delay=0, outcome=outcome)
        return products, outcome
    products, outcome = asyncio.run(run())
    assert len(products) == 1 and products[0].offers[0].variant_key == KEY
    assert outcome['errors'] == 0 and outcome['product_pages'] == outcome['evidence_requests'] == 1
    assert len(requested) == 4  # two collections, one detail, one independent JSON
    parser = TheCircleParser()
    assert parser.parse_listing_page(single_listing(full_price=True), ORIGIN + '/sale/') == []
    assert parser.get_next_page_url(single_listing(full_price=True), ORIGIN + '/sale/') is None


@pytest.mark.parametrize('mode', ['page_limit', 'detail_budget', 'blocked_evidence'])
def test_existing_page_detail_and_http_error_gates_remain_incomplete(mode):
    html, _ = capture()
    requested = []
    def handler(request):
        requested.append(str(request.url))
        if request.url.path.endswith('.ajax'):
            return httpx.Response(403)
        if request.url.path.endswith('.html'):
            return httpx.Response(200, text=html)
        text = (FIXTURES / 'snow-1.html').read_text() if mode == 'page_limit' else single_listing()
        return httpx.Response(200, text=text)
    async def run():
        outcome = {'errors': 0, 'pages': 0}
        url = ORIGIN + ('/snow/' if mode == 'page_limit' else '/sale/')
        store = RetailerConfig('Circle', 'www.thecirclewhistler.com', [url], parser_type='thecircle', currency='CAD')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            products = await fetch_products(store, TheCircleParser(), client, semaphore=asyncio.Semaphore(1),
                                            delay=0, outcome=outcome, max_pages=1,
                                            max_product_pages=0 if mode == 'detail_budget' else 500)
        return products, outcome
    products, outcome = asyncio.run(run())
    assert products == [] and outcome['errors'] == 1
    assert outcome['collections'][0]['status'] == {
        'page_limit': 'page_limit', 'detail_budget': 'parse_error', 'blocked_evidence': 'product_http_error'}[mode]
    assert len(requested) == (3 if mode == 'blocked_evidence' else 1)


@pytest.mark.parametrize(('first', 'second'), [(False, True), (True, False), (False, 'false')])
def test_backorder_aliases_cannot_hide_conflicting_or_malformed_negative_stock(first, second):
    html, raw = capture()
    for stock in (raw['stock'], raw['variants'][KEY]['stock']):
        stock.update(allow_backorders=first, allow_outofstock_sale=second)
    with pytest.raises(ValueError, match='backorder'):
        parse(html, raw)


@pytest.mark.parametrize('empty', ['', '   '])
def test_agreeing_empty_purchase_titles_are_not_product_identity(empty):
    html, raw = capture()
    soup = BeautifulSoup(html, 'html.parser')
    soup.select_one('h1.product__title').string = empty
    raw['title'] = empty
    with pytest.raises(ValueError, match='title'):
        parse(str(soup), raw)


def test_full_first_page_without_pagination_is_incomplete_not_a_singleton():
    soup = BeautifulSoup((FIXTURES / 'sale-1.html').read_text(), 'html.parser')
    soup.select_one('.pager').decompose()
    parser = TheCircleParser()
    with pytest.raises(ValueError, match='pagination'):
        parser.parse_listing_page(str(soup), ORIGIN + '/sale/')
    with pytest.raises(ValueError, match='pagination'):
        parser.get_next_page_url(str(soup), ORIGIN + '/sale/')


@pytest.mark.parametrize(('field', 'value'), [
    ('price_old_money_with_currency', 'C$49.99 CAD'), ('price_old_money', 'C$49.99'),
    ('price_old_incl', 49.99), ('price_old', None), ('price_old', True),
])
def test_absent_reference_requires_explicit_consistent_false_evidence(field, value):
    html, raw = capture('rainboot')
    raw['variants']['114987778']['price'][field] = value
    with pytest.raises((ValueError, TypeError)):
        parse(html, raw, raw['url'])


def test_explicit_no_reference_sibling_never_borrows_the_selected_variant_discount():
    html, raw = capture('rainboot')
    soup = BeautifulSoup(html, 'html.parser')
    sibling = raw['variants']['114987778']
    sibling['stock'].update(available=True, on_stock=True, level=1)
    soup.select_one('[data-vid="114987778"][data-availability]')['data-availability'] = '1'
    actual = detail_data(str(soup), raw['url'], json.dumps(raw))
    assert actual['variants']['114987778']['reference'] == 0
    offers = parse(str(soup), raw, raw['url'])[0].offers
    assert [offer.variant_key for offer in offers] == ['114987775']


@pytest.mark.parametrize('change', ['missing_endpoint_gallery', 'missing_html_gallery', 'wrong_top_image_id',
                                  'wrong_top_image_url', 'explicit_variant_image_conflict'])
def test_product_gallery_fallback_cannot_hide_explicit_or_unbound_image_conflicts(change):
    html, raw = capture('kelly')
    soup = BeautifulSoup(html, 'html.parser')
    if change == 'missing_endpoint_gallery':
        raw['images'] = [url for url in raw['images'] if '/54568425/' not in url]
    elif change == 'missing_html_gallery':
        soup.select_one('#prod_slider img[src*="/54568425/"]').decompose()
    elif change == 'wrong_top_image_id':
        raw['image_id'] = 54568429
    elif change == 'wrong_top_image_url':
        raw['image'] = raw['image'].replace('/54568425/', '/54568429/')
    else:
        raw['variants'][str(raw['vid'])]['image'] = 54568429
        soup.select_one('[data-vid="94619673"][data-availability]')['data-image'] = '54568429'
    with pytest.raises(ValueError, match='image'):
        parse(str(soup), raw, raw['url'])
