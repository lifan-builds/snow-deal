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
