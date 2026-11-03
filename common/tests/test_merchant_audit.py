import asyncio

import httpx

from deal_common.catalog.audit import audit_sample, select_sample, validate_product


def card():
    return dict(name='Drill kit', store='Shop', url='https://shop.example/products/drill',
                offer=dict(url='https://shop.example/products/drill?variant=42', variant_key='42',
                           current_price=100, original_price=200, options='M / Red'))


def raw():
    return dict(title='Drill kit', variants=[dict(id=42, price=10000, compare_at_price=20000,
                                                 options=['M', 'Red'], available=True, sku='SKU-42')])


def test_price_reference_identity_options_and_stock_checked_separately():
    assert validate_product(card(), raw(), 'USD')['status'] == 'match'
    for key, value in [('price', 9999), ('compare_at_price', None), ('available', False), ('options', ['S'])]:
        response = raw()
        response['variants'][0][key] = value
        assert validate_product(card(), response, 'USD')['status'] == 'mismatch'
    assert validate_product(card(), raw(), 'CAD')['checks']['currency'] is False
    assert validate_product(card(), {**raw(), 'title': 'Another drill'}, 'USD')['checks']['identity'] is False
    assert validate_product(card(), {**raw(), 'variants': []}, 'USD')['status'] == 'inconclusive'


def test_block_is_not_retried_or_counted_as_match():
    calls = []
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(403)
    results = asyncio.run(audit_sample([card(), card()], {'Shop':'shop.example'}, delay=0,
                                       transport=httpx.MockTransport(handler)))
    assert len(calls) == 1
    assert all(r['status'] == 'inconclusive' for r in results)


def test_currency_only_and_exact_variant_audit_with_no_ingestion_parser():
    def handler(request):
        return httpx.Response(200, json={'currency':'USD'} if request.url.path == '/cart.js' else raw())
    results = asyncio.run(audit_sample([card()], {'Shop':'shop.example'}, delay=0,
                                       transport=httpx.MockTransport(handler)))
    assert results[0]['status'] == 'match'
    assert 'cart' not in results[0]
    assert results[0]['merchant']['sku'] == 'SKU-42'


def test_sample_is_reproducible_distinct_and_keeps_top_ten():
    cards = [{**card(), 'url':f'https://shop.example/products/{i}'} for i in range(100)]
    a = select_sample(cards)
    assert a == select_sample(cards) and a[:10] == cards[:10]
    assert len({c['url'] for c in a}) == 30


def test_declared_price_metadata_is_not_mistaken_for_a_variant_choice():
    response = raw()
    response['options'] = [{'name':'Size'}, {'name':'Color'}, {'name':'Retail Price'}]
    response['variants'][0]['options'].append('Retail: $200')
    result = validate_product(card(), response, 'USD')
    assert result['status'] == 'match' and result['merchant']['raw_options'][-1] == 'Retail: $200'
    response['options'][-1]['name'] = 'Package'
    assert validate_product(card(), response, 'USD')['checks']['options'] is False


def test_rate_limit_waits_as_requested_before_retrying(monkeypatch):
    waits, calls = [], []
    async def sleep(seconds):
        waits.append(seconds)
    monkeypatch.setattr("deal_common.http.asyncio.sleep", sleep)
    def handler(request):
        calls.append(request.url.path)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json={"currency": "USD"} if request.url.path == "/cart.js" else raw())
    results = asyncio.run(audit_sample([card()], {"Shop": "shop.example"}, delay=5,
                                      transport=httpx.MockTransport(handler)))
    assert results[0]["status"] == "match"
    assert calls == ["/cart.js", "/cart.js", "/products/drill.js"]
    assert waits == [5, 7, 5, 5]


def test_rate_limit_beyond_wait_budget_stops_the_host():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(429, headers={"Retry-After": "120"})
    results = asyncio.run(audit_sample([card(), card()], {"Shop": "shop.example"}, delay=0,
                                      transport=httpx.MockTransport(handler)))
    assert calls == ["/cart.js"]
    assert all(r["status"] == "inconclusive" for r in results)


def test_persistent_rate_limit_stops_after_bounded_retries():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(429, headers={"Retry-After": "0"})
    results = asyncio.run(audit_sample([card(), card()], {"Shop": "shop.example"}, delay=0,
                                      transport=httpx.MockTransport(handler)))
    assert calls == ["/cart.js"] * 4
    assert all(r["status"] == "inconclusive" for r in results)
