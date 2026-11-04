"""Bolton's observed purchase markup and category completeness boundaries."""
import asyncio
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from bs4 import BeautifulSoup
from deal_common.catalog.audit import audit_sample, validate_bolton_product
from deal_common.catalog.refresh import normalize, refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig
from deal_common.parsers.bolton import BoltonParser, detail_data, offer_destination
from tool_deals.catalog import CATALOG

URL = 'https://www.boltontool.com/1-magpress-mp40-6zu5bla5r'
COLLECTION = 'https://www.boltontool.com/drill-presses'
KEY = '30168|FGTRCTCK|1-magpress-mp40-6zu5bla5r'
FIXTURE = Path(__file__).with_name('fixtures') / 'bolton-drill.html'


def detail(*, restricted=False):
    soup = BeautifulSoup(FIXTURE.read_text(), 'html.parser')
    if not restricted:
        soup.select_one('.warehouse-relocation-banner').decompose()
    return str(soup)


def listing(*, slugs=('1-magpress-mp40-6zu5bla5r',), page=1, total=None, pages=1, start=1):
    total = len(slugs) if total is None else total
    end = start + len(slugs) - 1 if total else 0
    start = start if total else 0
    return ('<div id="content">' + ''.join(
        '<div class="product-thumb"><div class="caption"><h5>'
        f'<a href="https://www.boltontool.com/drill-presses/{slug}">Magnetic Drill Press Machine</a>'
        '</h5><span class="price-new">$374.22</span><span class="price-old">$748.44</span>'
        '<b><div>In stock</div></b></div></div>' for slug in slugs)
        + f'<div class="col-sm-6 text-right">Showing {start} to {end} of {total} ({pages} Pages)</div>'
        + (f'<ul class="pagination"><li><a href="{COLLECTION}?page={page+1}">&gt;</a></li></ul>'
           if page < pages else '') + '</div>')


def test_single_unit_price_matches_model_canonical_and_stock():
    product = BoltonParser().parse_product_page(detail(), COLLECTION + '/1-magpress-mp40-6zu5bla5r')[0]
    offer = product.offers[0]
    assert (product.current_price, product.original_price) == (374.22, 748.44)
    assert (offer.current_price, offer.original_price) == (374.22, 748.44)
    assert (offer.variant_key, offer.options, offer.url) == (KEY, 'Model FGTRCTCK', URL)
    assert offer.availability == 'in_stock' and product.brand is None
    assert offer.image_url == 'https://content.toolots.com/media/catalog/product//6/z/6zu5bla5r_3359895.jpg'
    # The observed 10+/20+ unit bulk prices must never become a single-unit price.
    assert '$229.99' in detail() and '$226.99' in detail()
    assert detail_data(detail(), URL)['price'] == 374.22


def test_active_relocation_notice_overrides_instock_and_past_restoration_date():
    html = detail(restricted=True)
    assert 'October 1, 2026' in html
    for freight in ('', '<div data-freight-services>Optional Freight Delivery Services</div>'):
        with pytest.raises(ValueError, match='warehouse shipping restriction'):
            detail_data(html.replace('</div>', freight + '</div>', 1), URL)


@pytest.mark.parametrize('selector,attribute,value', [
    ('[itemprop=priceCurrency]', 'content', 'CAD'),
    ('[itemprop=price]', 'content', '374.23'),
    ('[itemprop=sku]', 'content', 'OTHER'),
    ('[itemprop=name]', 'content', 'Different machine'),
    ('link[rel=canonical]', 'href', 'https://other.example/1-magpress-mp40-6zu5bla5r'),
    ('link[rel=canonical]', 'href', URL + '?variant=1'),
    ('#product input[name=product_id]', 'value', ''),
    ('#product input[name=quantity]', 'value', '10'),
    ('#product input[name=quantity]', 'min', '10'),
    ('#product #button-cart', 'disabled', ''),
])
def test_ambiguous_identity_currency_purchase_and_price_fail(selector, attribute, value):
    soup = BeautifulSoup(detail(), 'html.parser')
    soup.select_one(selector)[attribute] = value
    with pytest.raises(ValueError):
        detail_data(str(soup), URL)


@pytest.mark.parametrize('selector', ['.product-detail-title', '.product-detail-meta',
                                    '[itemprop=priceCurrency]', '.product-detail-stock',
                                    '#product input[name=product_id]', '#product #button-cart'])
def test_missing_purchase_evidence_fails(selector):
    soup = BeautifulSoup(detail(), 'html.parser')
    soup.select_one(selector).decompose()
    with pytest.raises(ValueError):
        detail_data(str(soup), URL)


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-1', '0', '$,374.22', '$3,74.22', '$374.221'])
def test_malformed_prices_fail(value):
    soup = BeautifulSoup(detail(), 'html.parser')
    for node in soup.select('.product-detail-price__current'):
        node.string = value
    with pytest.raises(ValueError):
        detail_data(str(soup), URL)


@pytest.mark.parametrize('attribute,value', [('availability', 'OutOfStock'), ('availability', 'PreOrder'),
                                          ('itemCondition', 'UsedCondition')])
def test_unavailable_or_used_products_are_not_eligible(attribute, value):
    soup = BeautifulSoup(detail(), 'html.parser')
    soup.select_one(f'[itemprop={attribute}]')['href'] = 'https://schema.org/' + value
    assert BoltonParser().parse_product_page(str(soup), URL) == []


def test_visible_stock_conflicts_and_unknown_stock_are_not_confirmed():
    for stock in ('Out Of Stock', 'Unknown', 'Available to order'):
        soup = BeautifulSoup(detail(), 'html.parser')
        soup.select_one('.product-detail-stock').string = stock
        assert BoltonParser().parse_product_page(str(soup), URL) == []
    assert BoltonParser().parse_product_page(detail().replace('https://schema.org/InStock',
                                                             'https://other.example/InStock'), URL) == []


def test_unresolved_options_and_conflicting_prices_fail():
    soup = BeautifulSoup(detail(), 'html.parser')
    soup.select_one('#product').append(BeautifulSoup('<select name="option[45]"><option>220V</option></select>',
                                                   'html.parser'))
    with pytest.raises(ValueError, match='Unresolved'):
        detail_data(str(soup), URL)
    soup = BeautifulSoup(detail(), 'html.parser')
    soup.select('.product-detail-price__current')[1].string = '$1'
    with pytest.raises(ValueError, match='sale price'):
        detail_data(str(soup), URL)


def test_no_reference_or_full_price_is_not_a_deal_and_freight_is_disclosed():
    soup = BeautifulSoup(detail(), 'html.parser')
    for node in soup.select('.product-detail-price__old'):
        node.decompose()
    assert BoltonParser().parse_product_page(str(soup), URL) == []
    assert BoltonParser().parse_product_page(detail().replace('$748.44', '$374.22'), URL) == []
    soup.select_one('#product').append(BeautifulSoup('<div data-freight-services>Optional Freight Delivery Services</div>',
                                                   'html.parser'))
    assert 'charges' in detail_data(str(soup), URL)['shipping_note']


def test_complete_pagination_counts_every_listing_and_resets_between_categories():
    parser = BoltonParser()
    assert len(parser.parse_listing_page(listing(), COLLECTION)) == 1
    assert parser.get_next_page_url(listing(), COLLECTION) is None
    first = listing(slugs=('a', 'b'), total=3, pages=2)
    assert len(parser.parse_listing_page(first, COLLECTION)) == 2
    second_url = parser.get_next_page_url(first, COLLECTION)
    assert second_url == COLLECTION + '?page=2'
    second = listing(slugs=('c',), total=3, page=2, pages=2, start=3)
    assert len(parser.parse_listing_page(second, second_url)) == 1
    assert parser.get_next_page_url(second, second_url) is None
    assert parser.parse_listing_page(listing(slugs=()), 'https://www.boltontool.com/other') == []


@pytest.mark.parametrize('case', ['short', 'duplicate', 'total', 'pages', 'cross-page-duplicate',
                                'next-host', 'next-path', 'next-page', 'missing-count', 'invalid-page'])
def test_incomplete_or_repeated_pages_never_become_complete(case):
    parser = BoltonParser()
    url = COLLECTION
    html = listing(slugs=('a', 'b'), total=3, pages=2)
    if case in {'total', 'pages', 'cross-page-duplicate'}:
        parser.parse_listing_page(html, url)
        url = COLLECTION + '?page=2'
        html = listing(slugs=('c',), total=4 if case == 'total' else 3,
                       pages=3 if case == 'pages' else 2, page=2, start=3)
        if case == 'cross-page-duplicate':
            html = html.replace('/c"', '/a"')
    elif case == 'short':
        html = html.replace('Showing 1 to 2', 'Showing 1 to 3')
    elif case == 'duplicate':
        html = html.replace('/b"', '/a"')
    elif case == 'next-host':
        html = html.replace(COLLECTION + '?page', 'https://other.example/drill-presses?page')
    elif case == 'next-path':
        html = html.replace(COLLECTION + '?page', 'https://www.boltontool.com/other?page')
    elif case == 'next-page':
        html = html.replace('?page=2', '?page=3')
    elif case == 'missing-count':
        html = '<html>Challenge</html>'
    else:
        url += '?page=0'
    with pytest.raises(ValueError):
        parser.parse_listing_page(html, url)


@pytest.mark.parametrize('url,key', [(URL+'?variant=1', KEY), (URL+'#buy', KEY),
                                   (URL.replace('https:', 'http:'), KEY),
                                   (URL.replace('www.boltontool.com', 'evil.example'), KEY),
                                   (URL, KEY.replace('30168', 'other')), (URL, KEY+'|'),
                                   (URL+'/other', KEY), ('https://[invalid', KEY)])
def test_destination_rejects_wrong_or_unsafe_exact_identity(url, key):
    assert not offer_destination(url, key)


def test_normalization_and_independent_audit_bind_the_same_offer():
    product = BoltonParser().parse_product_page(detail(), URL)[0]
    row = normalize([product], CATALOG, 'www.boltontool.com', parser_type='bolton')[0]
    card = {**row, 'store': 'Bolton Tools', 'offer': row['offers'][0]}
    merchant = detail_data(detail(), URL)
    assert validate_bolton_product(card, merchant)['status'] == 'match'
    card['offer']['variant_key'] = KEY.replace('30168', '30169')
    assert validate_bolton_product(card, merchant)['checks']['identity'] is False
    product.offers[0].url += '?variant=1'
    assert normalize([product], CATALOG, 'www.boltontool.com', parser_type='bolton') == []


def test_refresh_preserves_prior_success_under_relocation_and_audit_refetches(tmp_path):
    source = RetailerConfig('Bolton Tools', 'www.boltontool.com', [COLLECTION], parser_type='bolton')
    catalog = replace(CATALOG, sources=(source,))
    path = tmp_path / 'catalog.db'
    requested = []
    def handler(request):
        requested.append(str(request.url))
        return httpx.Response(200, text=listing() if str(request.url) == COLLECTION else detail())
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(handler)))
    before = read_sources(path, 'tools')[0]
    assert report[0]['status'] == 'complete' and len(before['products']) == 1
    assert requested == [COLLECTION, COLLECTION+'/1-magpress-mp40-6zu5bla5r']
    def restricted(request):
        return httpx.Response(200, text=listing() if str(request.url) == COLLECTION else detail(restricted=True))
    report = asyncio.run(refresh(catalog, path, delay=0, transport=httpx.MockTransport(restricted)))
    after = read_sources(path, 'tools')[0]
    assert report[0]['status'] == 'incomplete'
    assert before['successful_at'] == after['successful_at'] and before['products'] == after['products']
    card = {**before['products'][0], 'store': 'Bolton Tools', 'offer': before['products'][0]['offers'][0]}
    rows = asyncio.run(audit_sample([card], {'Bolton Tools': 'www.boltontool.com'}, delay=0,
                                   transport=httpx.MockTransport(handler)))
    assert rows[0]['status'] == 'match' and requested[-1] == URL
    rows = asyncio.run(audit_sample([card], {'Bolton Tools': 'www.boltontool.com'}, delay=0,
                                   transport=httpx.MockTransport(restricted)))
    assert rows[0]['status'] == 'inconclusive'
