"""Configured snow routing with a factual Circle detail/endpoint pair, offline."""
import asyncio
import json
from pathlib import Path

import httpx
from aggregator.config import STORES

from aggregator import scraper

FIXTURES = Path(__file__).resolve().parents[3] / 'common/tests/fixtures/thecircle'
ORIGIN = 'https://www.thecirclewhistler.com'
PRODUCT_URL = ORIGIN + '/jackson-mips-helmet.html'


def configured_scrape(monkeypatch, *, corrupt_evidence=False):
    html = (FIXTURES / 'jackson.html').read_text()
    payload = json.loads((FIXTURES / 'jackson.json').read_text())
    if corrupt_evidence:
        # The canonical product ID no longer agrees with its native form.
        payload['id'] = 999
    requested = []

    def handler(request):
        assert request.method == 'GET'
        assert request.url.scheme == 'https' and request.url.host == 'www.thecirclewhistler.com'
        requested.append(str(request.url))
        if str(request.url) == PRODUCT_URL:
            return httpx.Response(200, text=html)
        if str(request.url) == PRODUCT_URL.removesuffix('.html') + '.ajax':
            return httpx.Response(200, json=payload)
        assert request.url.path in {'/sale/', '/snow/'}
        # Synthetic singleton collection; product facts come from the retained pair.
        return httpx.Response(200, text=(
            f'<link rel="canonical" href="{request.url}"><div id="ls-product-results">'
            f'<div class="prod-card" data-product-id="60540290" data-url="{PRODUCT_URL}">'
            f'<div class="title"><a href="{PRODUCT_URL}">Jackson Mips Helmet 2025</a></div>'
            '<div class="product_brand">Giro</div><div class="price">'
            '<span class="slashed">C$269.99</span>C$81.00</div></div></div>'
        ))

    real_client = httpx.AsyncClient

    def mock_client(**kwargs):
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    async def unexpected_browser(*args, **kwargs):
        raise AssertionError('The reviewed Circle source must use the static evidence path')

    monkeypatch.setattr(scraper.httpx, 'AsyncClient', mock_client)
    monkeypatch.setattr(scraper, 'scrape_store_browser', unexpected_browser)
    store = next(store for store in STORES if store.name == 'The Circle Whistler')
    outcomes = {}
    deals = asyncio.run(scraper.scrape_all(stores=[store], delay=0, outcomes=outcomes))
    return deals, outcomes[store.name], requested


def test_configured_circle_scrape_preserves_exact_cad_offer(monkeypatch):
    deals, outcome, requested = configured_scrape(monkeypatch)

    assert len(deals) == 1
    deal = deals[0]
    assert (deal.store, deal.name, deal.category, deal.brand, deal.currency, deal.sizes) == (
        'The Circle Whistler', 'Jackson Mips Helmet 2025', 'helmets', 'giro', 'CAD', 'XL')
    assert (deal.url, deal.current_price, deal.original_price) == (PRODUCT_URL, 81, 269.99)
    assert len(deal.offers) == 1  # Unavailable L sibling cannot become an exact-size offer.
    offer = deal.offers[0]
    assert (offer.variant_key, offer.size, offer.options, offer.availability,
            offer.current_price, offer.original_price, offer.url) == (
        '100724076', 'XL', 'Color: Matte Black / Size: XL', 'in_stock',
        81, 269.99, PRODUCT_URL + '?id=100724076')
    assert '/59676659/' in offer.image_url and deal.image_url == offer.image_url
    assert outcome['errors'] == 0
    assert [collection['status'] for collection in outcome['collections']] == ['complete', 'complete']
    assert outcome['product_pages'] == outcome['evidence_requests'] == 1
    assert requested == [ORIGIN + '/sale/', PRODUCT_URL,
                         PRODUCT_URL.removesuffix('.html') + '.ajax', ORIGIN + '/snow/']


def test_configured_circle_conflicting_endpoint_marks_source_incomplete(monkeypatch):
    deals, outcome, requested = configured_scrape(monkeypatch, corrupt_evidence=True)

    assert deals == []
    assert outcome['errors'] > 0
    assert any(collection['status'] == 'parse_error' for collection in outcome['collections'])
    assert PRODUCT_URL.removesuffix('.html') + '.ajax' in requested
