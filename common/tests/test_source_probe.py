import asyncio
import importlib.util
import json
from pathlib import Path

import pytest
from deal_common.parsers.shopify import ShopifyParser

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('probe_sources', ROOT / 'scripts/probe_sources.py')
probe_sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe_sources)


@pytest.mark.parametrize('tags', [['ebike_block_ship', 'used'], 'ebike_block_ship, used'])
def test_shopify_keeps_explicit_tags_for_catalog_scope(tags):
    item = {'title': 'Mountain Bike', 'handle': 'bike', 'tags': tags,
            'variants': [{'id': 1, 'available': True, 'price': '500', 'compare_at_price': '2000'}]}
    product = ShopifyParser().parse_listing_page(json.dumps({'products': [item]}),
                                                 'https://shop.example/collections/bikes')[0]
    assert product.tags == ('ebike_block_ship', 'used')


def test_probe_preserves_previous_evidence_and_uses_real_shared_refresh(tmp_path, monkeypatch):
    seen = []
    async def refresh(catalog, path, **kwargs):
        from deal_common.catalog.storage import save_source
        seen.append((catalog.sources[0].parser_type, kwargs['max_pages']))
        save_source(path, catalog.slug, catalog.sources[0].name, '2026-11-02T00:00:00+00:00',
                    [], 'incomplete', {'errors': 1})
        return [{'source': catalog.sources[0].name, 'status': 'incomplete', 'errors': 1}]
    monkeypatch.setattr(probe_sources, 'refresh', refresh)
    candidates = [{'catalog': 'tools', 'name': 'Grizzly', 'domain': 'www.grizzly.com',
                   'parser_type': 'grizzly', 'scrape_urls': ['https://www.grizzly.com/outlet-specials/shop-all']}]
    out = tmp_path / 'probe'
    rows = asyncio.run(probe_sources.probe(candidates, out, max_pages=30))
    assert seen == [('grizzly', 30)]
    assert rows[0]['disposition'] == 'no-eligible-complete-snapshot'
    original = (out / 'report.json').read_text()
    with pytest.raises(ValueError, match='preserve'):
        asyncio.run(probe_sources.probe(candidates, out))
    assert (out / 'report.json').read_text() == original


def candidate_products(count=45):
    result = []
    for index in range(count):
        url = f'https://candidate.example/products/saw-{index:02d}'
        offer = {'variant_key': str(index + 1000), 'url': url + '?variant=' + str(index + 1000),
                 'current_price': 250 + index if index < 35 else 850 + index,
                 'original_price': 1000, 'size': None, 'options': '', 'availability': 'in_stock',
                 'image_url': None, 'availability_note': ''}
        # Extra variants cannot change the established one-offer-per-listing sample.
        alternate = {**offer, 'variant_key': str(index + 2000),
                     'url': url + '?variant=' + str(index + 2000), 'current_price': offer['current_price'] + 1}
        unknown = {**offer, 'variant_key': str(index + 3000), 'current_price': 10, 'availability': 'unknown'}
        result.append({'name': f'Saw {index:02d}', 'url': url, 'brand': 'Test',
                       'category': 'Power tools', 'format': '', 'platform': '',
                       'offers': [offer, alternate, unknown]})
    return result


def candidate_manifest():
    return [{'catalog': 'tools', 'name': 'Candidate', 'domain': 'candidate.example',
             'scrape_urls': ['https://candidate.example/collections/tools?currency=USD']}]


def mock_refresh(monkeypatch, *, status='complete', products=None):
    from datetime import UTC, datetime

    async def refresh(catalog, path, **kwargs):
        from deal_common.catalog.storage import save_source
        errors = int(status != 'complete')
        save_source(path, catalog.slug, catalog.sources[0].name, datetime.now(UTC).isoformat(),
                    candidate_products() if products is None else products, status, {'errors': errors})
        return [{'source': catalog.sources[0].name, 'status': status, 'errors': errors}]
    monkeypatch.setattr(probe_sources, 'refresh', refresh)


def test_merchant_selection_covers_all_deep_listings_and_preserves_fixed_sample():
    from datetime import UTC, datetime

    from deal_common.catalog.audit import select_sample

    sources = [{'name': 'Candidate', 'successful_at': datetime.now(UTC).isoformat(),
                'products': candidate_products()}]
    filters = {'min_reference': 200, 'min_discount': 0, 'max_price': 0, 'stock': True, 'page': 1}
    cards = probe_sources.all_cards(sources, filters)
    fixed = select_sample(cards, 42)
    selected, population, fixed_count, deep_count = probe_sources.merchant_selection(sources, filters, 42)
    selected_keys = {card['offer']['variant_key'] for card in selected}
    assert population == 45 and fixed_count == 30 and deep_count == 35
    assert {card['offer']['variant_key'] for card in fixed} <= selected_keys
    assert {str(1000 + i) for i in range(35)} <= selected_keys
    assert len(selected_keys) == len(selected)
    assert all(1000 <= int(key) < 1045 for key in selected_keys)
    assert selected[:30] == fixed
    assert probe_sources.merchant_selection(sources, filters, 42)[0] == selected


def test_audited_probe_writes_source_receipt_immediately_and_keeps_old_output(tmp_path, monkeypatch):
    mock_refresh(monkeypatch)
    seen = []
    async def audit(cards, domains, *, delay):
        seen.append((cards, domains, delay))
        return [{'name': card['name'], 'offer': card['offer'], 'status': 'match', 'checks': {'price': True}}
                for card in cards]
    monkeypatch.setattr(probe_sources, 'audit_sample', audit)
    out = tmp_path / 'audited'
    rows = asyncio.run(probe_sources.probe(candidate_manifest(), out, audit_merchants=True, seed=42))
    metadata = rows[0]['merchant_audit']
    receipt = json.loads((out / metadata['receipt']).read_text())
    assert receipt['passed'] and receipt['refresh_complete'] and receipt['seed'] == 42
    assert receipt['population'] == 45 and receipt['fixed_sample_size'] == 30
    assert receipt['deep_selected_listings'] == 35
    assert receipt['sample_size'] == receipt['selected_offers'] == len(seen[0][0])
    assert receipt['match'] == receipt['sample_size'] and receipt['mismatch'] == receipt['inconclusive'] == 0
    assert receipt['method'] == 'top10-plus-seeded20-plus-all-deep-listings-v1'
    assert receipt['results'] and seen[0][1:] == ({'Candidate': 'candidate.example'}, 2)
    assert rows[0]['disposition'] == 'merchant-audited-needs-review'
    original = (out / metadata['receipt']).read_bytes()
    with pytest.raises(ValueError, match='preserve'):
        asyncio.run(probe_sources.probe(candidate_manifest(), out, audit_merchants=True, seed=42))
    assert (out / metadata['receipt']).read_bytes() == original and len(seen) == 1


@pytest.mark.parametrize('failure', ['mismatch', 'inconclusive', 'empty-results', 'short-results'])
def test_failed_or_missing_merchant_results_fail_admission_and_remain_in_receipt(tmp_path, monkeypatch, failure):
    mock_refresh(monkeypatch)
    async def audit(cards, domains, *, delay):
        if failure == 'empty-results':
            return []
        results = [{'status': 'match'} for _ in cards]
        if failure == 'short-results':
            return results[:-1]
        results[-1] = {'status': failure, 'reason': 'Dated merchant evidence did not match'}
        return results
    monkeypatch.setattr(probe_sources, 'audit_sample', audit)
    out = tmp_path / 'failed'
    rows = asyncio.run(probe_sources.probe(candidate_manifest(), out, audit_merchants=True))
    receipt = json.loads((out / rows[0]['merchant_audit']['receipt']).read_text())
    assert rows[0]['disposition'] == 'merchant-audit-failed' and not receipt['passed']
    if failure in {'mismatch', 'inconclusive'}:
        assert receipt[failure] == 1 and receipt['results'][-1]['reason']
    else:
        assert receipt['sample_size'] < receipt['selected_offers']


@pytest.mark.parametrize(('status', 'products', 'reason'), [
    ('incomplete', None, 'Source refresh incomplete'),
    ('complete', [], 'No eligible fresh in-stock offers'),
])
def test_incomplete_or_empty_candidates_do_not_start_audit(tmp_path, monkeypatch, status, products, reason):
    mock_refresh(monkeypatch, status=status, products=products)
    async def audit(*args, **kwargs):
        pytest.fail('No merchant request belongs to an incomplete or empty candidate')
    monkeypatch.setattr(probe_sources, 'audit_sample', audit)
    out = tmp_path / 'not-auditable'
    rows = asyncio.run(probe_sources.probe(candidate_manifest(), out, audit_merchants=True))
    receipt = json.loads((out / rows[0]['merchant_audit']['receipt']).read_text())
    assert not receipt['passed'] and receipt['sample_size'] == 0 and receipt['reason'].startswith(reason)


@pytest.mark.parametrize(('opt_in', 'passed', 'expected'), [(True, True, 0), (True, False, 1), (False, False, 0)])
def test_cli_gates_exit_status_only_when_audit_was_requested(tmp_path, monkeypatch, opt_in, passed, expected):
    manifest = tmp_path / 'candidates.json'
    manifest.write_text(json.dumps(candidate_manifest()))
    seen = []
    async def probe(candidates, output, **kwargs):
        seen.append(kwargs)
        return [{'merchant_audit': {'passed': passed}}]
    monkeypatch.setattr(probe_sources, 'probe', probe)
    argv = ['probe_sources.py', str(manifest), '--output', str(tmp_path / 'new'), '--max-pages', '30', '--seed', '123']
    if opt_in:
        argv.append('--audit-merchants')
    monkeypatch.setattr(probe_sources.sys, 'argv', argv)
    assert probe_sources.main() == expected
    assert seen == [{'max_pages': 30, 'audit_merchants': opt_in, 'seed': 123}]
