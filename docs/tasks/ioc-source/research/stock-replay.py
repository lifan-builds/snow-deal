"""Replay retained public IOC feeds; never request or renew observations."""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
BASELINE_COMMIT = 'b19cd0ccffe6c70e7eb5e6449d4fdb7da0c6bdad'
sys.path[:0] = [str(ROOT / path) for path in ('common', 'catalogs/tools/src')]

from deal_common.catalog.query import query
from deal_common.catalog.refresh import normalize
from deal_common.parsers.shopify import ShopifyParser
from tool_deals.catalog import CATALOG


def main():
    source = subprocess.check_output(
        ['git', 'show', f'{BASELINE_COMMIT}:common/deal_common/parsers/availability.py'], cwd=ROOT, text=True)
    with tempfile.TemporaryDirectory(prefix='ioc-availability-replay-') as temporary:
        baseline_path = Path(temporary) / 'availability_baseline.py'
        baseline_path.write_text(source)
        spec = importlib.util.spec_from_file_location('ioc_availability_baseline', baseline_path)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
    directory = ROOT / '.local/source-expansion/ioc-20261106-raw'
    inputs, old, new = [], [], []
    for filename in ('all-welders', 'plasma-cutters'):
        path = directory / (filename + '.json')
        body = path.read_text()
        url = f'https://www.weldingsuppliesfromioc.com/collections/{filename}?currency=USD'
        with patch('deal_common.parsers.shopify.shipping_notice', baseline.shipping_notice):
            previous = ShopifyParser().parse_listing_page(body, url)
        current = ShopifyParser().parse_listing_page(body, url)
        assert len(previous) == len(current)
        old.extend(previous)
        new.extend(current)
        inputs.append({'path': str(path.relative_to(ROOT)),
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'raw_products': len(json.loads(body)['products']),
                       'parsed_discounted': len(current)})
    expected = json.loads((Path(__file__).parent / 'independent-notice-review.json').read_text())['rows']
    expected_ids = {o['variant_key'] for row in expected for o in row['offers']}
    changed = []
    for previous, current in zip(old, new, strict=True):
        before, after = asdict(previous), asdict(current)
        if before == after:
            continue
        assert len(before['offers']) == len(after['offers'])
        for prior_offer, offer in zip(before['offers'], after['offers'], strict=True):
            assert prior_offer['availability'] == 'in_stock'
            assert offer['availability'] == 'unknown'
            assert offer['availability_note'].startswith('Retailer shipping notice: These ')
            assert offer['variant_key'] in expected_ids
            assert offer == {**prior_offer, 'availability': 'unknown',
                             'availability_note': offer['availability_note']}
        assert after == {**before, 'offers': after['offers']}
        changed.append({'name': current.name, 'url': current.url,
                        'offers': [{'variant_key': o.variant_key, 'before_stock': 'in_stock',
                                    'after_stock': o.availability, 'notice': o.availability_note,
                                    'price': o.current_price, 'reference': o.original_price,
                                    'url': o.url} for o in current.offers]})
    changed_ids = {o['variant_key'] for row in changed for o in row['offers']}
    assert changed_ids == expected_ids and len(changed) == 6
    old_rows = normalize(old, CATALOG, 'www.weldingsuppliesfromioc.com')
    new_rows = normalize(new, CATALOG, 'www.weldingsuppliesfromioc.com')
    assert len(old_rows) == len(new_rows) == 195
    for previous, current in zip(old_rows, new_rows, strict=True):
        previous = {**previous, 'offers': [{k: v for k, v in o.items()
                                          if k not in {'availability', 'availability_note'}}
                                         for o in previous['offers']]}
        current = {**current, 'offers': [{k: v for k, v in o.items()
                                        if k not in {'availability', 'availability_note'}}
                                       for o in current['offers']]}
        assert previous == current
    # Query at the historical capture day without updating or saving any source.
    from datetime import UTC, datetime
    observed = datetime(2026, 11, 6, 21, tzinfo=UTC)
    filters = {'min_reference': 200, 'max_price': 0, 'min_discount': 0, 'stock': True, 'page': 1}
    def population(products, discount=0):
        sources = [{'name': 'Welding Supplies from IOC', 'successful_at': observed.isoformat(),
                    'products': products, 'status': 'complete'}]
        return query(sources, {**filters, 'min_discount': discount}, now=observed)['total']
    report = {'scope': 'Offline comparison of retained public feeds using committed availability versus '
                       'candidate availability, under the same candidate classifier. Query uses an explicit '
                       'historical capture-day clock; no saved observation or freshness is renewed. '
                       'Not source admission, checkout or fresh endpoint evidence.',
              'baseline_commit': BASELINE_COMMIT,
              'availability_sha256': hashlib.sha256(
                  (ROOT / 'common/deal_common/parsers/availability.py').read_bytes()).hexdigest(),
              'inputs': inputs, 'parsed_products': len(new), 'normalized_products': len(new_rows),
              'changed_stock_products': len(changed), 'all_other_parsed_and_normalized_facts_exact': True,
              'historical_stock_population_before': population(old_rows),
              'historical_stock_population_after': population(new_rows),
              'historical_deep_stock_before': population(old_rows, 40),
              'historical_deep_stock_after': population(new_rows, 40),
              'changed': changed, 'passed': True}
    output = Path(__file__).with_suffix('.json')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'changed', 'scope'}}, indent=2))


if __name__ == '__main__':
    main()
