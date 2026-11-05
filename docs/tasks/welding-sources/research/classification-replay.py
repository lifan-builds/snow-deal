"""Offline replay of the explicitly retained public inputs; never writes a DB."""
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / 'common'), str(ROOT / 'catalogs/tools/src')]

from deal_common.catalog.refresh import normalize
from deal_common.catalog.storage import read_sources
from deal_common.models import Product
from deal_common.offers import VariantOffer, discount
from deal_common.parsers.harvey import shipping_notice as old_notice
from deal_common.parsers.shopify import ShopifyParser
from tool_deals.catalog import CATALOG, classify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classification(result):
    return asdict(result) if result else None


def product(raw, domain):
    return Product(raw['title'], 'https://' + domain + '/products/' + raw['handle'], 1, 2,
                   product_type=raw['product_type'], brand=raw['vendor'], tags=tuple(raw['tags']))


def facts(row):
    if row is None:
        return None
    return {
        'category': row['category'], 'format': row['format'], 'brand': row['brand'],
        'offers': len(row['offers']),
        'stock': dict(Counter(o['availability'] for o in row['offers'])),
        'reference_200_confirmed_stock': any(
            o['availability'] == 'in_stock' and o['original_price'] >= 200 for o in row['offers']),
        'deep_40_reference_200_confirmed_stock': any(
            o['availability'] == 'in_stock' and o['original_price'] >= 200
            and discount(o['current_price'], o['original_price']) >= 40 for o in row['offers']),
    }


def evidence(p, result):
    tags = {tag.casefold() for tag in p.tags}
    if result:
        if tags & {'multiprocess welder', 'mig welder', 'tig welder', 'stick welder', 'plasma cutter'}:
            return 'Precise welding-machine/plasma-cutter tag; primary-title and negative gates passed.'
        if 'welding machine' in p.product_type.casefold() or p.product_type in {
                'Battery Powered Welder', 'Welder / Generator', 'Plasma Cutting Machine'}:
            return 'Explicit machine taxonomy; primary-title and negative gates passed.'
        if 'bundle' in p.name.casefold() and 'welding machine' in ' '.join(tags):
            return 'Explicit fixed bundle with full machine tag bound to its declared manufacturer tag.'
        return 'Existing recognized power-tool/workshop primary identity.'
    if tags & {'spool guns & wire feeders', 'wire feeders', 'wire feeder'}:
        return 'Negative standalone gun/feeder taxonomy; no explicit Wire Feeder Welder primary identity.'
    if re.search(r'\b(?:gun|liner|consumable|charger)\b', p.product_type, re.IGNORECASE):
        return 'Component/consumable/charger taxonomy and no complete machine identity.'
    if re.search(r'\bwire feed(?:ers?| units?)\b', p.name, re.IGNORECASE):
        return 'Standalone wire-feeder primary title overrides misleading machine taxonomy/tag.'
    return 'No currently recognized primary equipment identity; collection/type alone is insufficient.'


def raw_feed(before, filename, domain):
    path = ROOT / '.local/source-expansion/welding-20261105' / filename
    digest = sha(path)
    raw = json.loads(path.read_text())
    content = json.dumps({'products': raw})
    collection = 'https://' + domain + '/collections/replay?currency=USD'
    with patch('deal_common.parsers.shopify.shipping_notice', old_notice):
        old_products = ShopifyParser().parse_listing_page(content, collection)
    new_products = ShopifyParser().parse_listing_page(content, collection)
    old_rows = {p['url']: p for p in normalize(old_products, before.CATALOG, domain)}
    new_rows = {p['url']: p for p in normalize(new_products, CATALOG, domain)}
    old_by_url = {p.url: asdict(p) for p in old_products}
    changed_offer_evidence = []
    for parsed in new_products:
        old = old_by_url[parsed.url]
        new = asdict(parsed)
        for old_offer, new_offer in zip(old['offers'], new['offers'], strict=True):
            if old_offer != new_offer:
                changed = [k for k in old_offer if old_offer[k] != new_offer[k]]
                assert set(changed) <= {'availability', 'availability_note'}, changed
                changed_offer_evidence.append({'url': parsed.url, 'before': old_offer, 'after': new_offer})
                old_offer.update({k: new_offer[k] for k in changed})
        assert old == new, parsed.url
    records = []
    counts = Counter()
    for item in raw:
        p = product(item, domain)
        old = classification(before.classify(p))
        new = classification(classify(p))
        counts[new['category'] if new else 'excluded'] += 1
        url = p.url + '?currency=USD'
        records.append({'id': str(item['id']), 'name': p.name, 'url': p.url,
                        'source_category': p.product_type, 'tags': list(p.tags),
                        'classification_before': old, 'classification_after': new,
                        'classification_evidence': evidence(p, new),
                        'normalized_before': facts(old_rows.get(url)),
                        'normalized_after': facts(new_rows.get(url))})
    assert sha(path) == digest
    return {
        'input': str(path.relative_to(ROOT)), 'sha256_unchanged': digest,
        'raw_products': len(raw), 'classified_after': dict(counts),
        'parsed_before': len(old_products), 'parsed_after': len(new_products),
        'normalized_before': len(old_rows), 'normalized_after': len(new_rows),
        'normalized_added': sorted(new_rows.keys() - old_rows.keys()),
        'normalized_removed': sorted(old_rows.keys() - new_rows.keys()),
        'normalized_changed': [
            {'url': url, 'before': facts(old_rows[url]), 'after': facts(new_rows[url])}
            for url in sorted(old_rows.keys() & new_rows.keys()) if old_rows[url] != new_rows[url]],
        'all_parser_fields_equal_except_reported_availability': True,
        'changed_offer_evidence': changed_offer_evidence,
        'normalized_stock_after': dict(Counter(o['availability'] for p in new_rows.values() for o in p['offers'])),
        'reference_200_confirmed_stock_products_after': sum(
            facts(p)['reference_200_confirmed_stock'] for p in new_rows.values()),
        'deep_40_reference_200_confirmed_stock_products_after': sum(
            facts(p)['deep_40_reference_200_confirmed_stock'] for p in new_rows.values()),
        'records': records,
    }


def public_snapshot(before):
    path = ROOT / '.local/release/tools-recall/production-42089645493/tools/site/data/catalog.db'
    digest = sha(path)
    sources = read_sources(path, 'tools')  # Explicitly read-only SQLite URI.
    total = 0
    changes = []
    for source in sources:
        for row in source['products']:
            total += 1
            p = Product(row['name'], row['url'], 1, 2, product_type=row['source_category'],
                        brand=row['brand'], offers=[VariantOffer(**offer) for offer in row['offers']])
            old = classification(before.classify(p))
            new = classification(classify(p))
            aliases = dict(CATALOG.brand_aliases)
            new_brand = aliases.get(row['brand'].casefold(), row['brand'])
            if old != new or new_brand != row['brand']:
                changes.append({'source': source['name'], 'name': row['name'], 'url': row['url'],
                                'before': old, 'after': new, 'old_brand': row['brand'], 'new_brand': new_brand})
    assert sha(path) == digest
    return {'input': str(path.relative_to(ROOT)), 'sha256_before_after': digest,
            'sources': len(sources), 'products': total, 'classification_or_alias_changes': changes,
            'database_opened_read_only': True,
            'limitation': 'Accepted-product snapshot retains source_category but not raw tags or rejected products. '
                          'This replay cannot recover previously rejected existing-source products.'}


def main():
    before = ModuleType('tools_before_welding')
    before.__file__ = str(ROOT / 'catalogs/tools/src/tool_deals/catalog.py')
    baseline = subprocess.check_output(['git', 'show', 'HEAD:catalogs/tools/src/tool_deals/catalog.py'], cwd=ROOT)
    exec(compile(baseline, before.__file__, 'exec'), before.__dict__)  # noqa: S102 -- Local Git baseline, never merchant code.
    report = {
        'baseline_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'baseline_classifier_sha256': hashlib.sha256(baseline).hexdigest(),
        'candidate_classifier_sha256': sha(ROOT / 'catalogs/tools/src/tool_deals/catalog.py'),
        'method': 'Pure retained-input replay; no HTTP, freshness restamping or database writes. '
                  'Every raw record classified independently of stock/discount; production parser/normalize '
                  'then retain actual direct discounts and available!=false. '
                  'Counts are provisional retained evidence, not source admission or live inventory.',
        'feeds': [raw_feed(before, 'bakers-with-grinders-products.json', 'bakersgas.com'),
                  raw_feed(before, 'cyberweld-machines-products.json', 'store.cyberweld.com')],
        'existing_public_snapshot': public_snapshot(before),
    }
    output = Path(__file__).with_name('classification-replay.json')
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({
        'feeds': [{k: value for k, value in feed.items() if k not in {
            'records', 'normalized_added', 'normalized_removed', 'normalized_changed', 'changed_offer_evidence'}}
                  for feed in report['feeds']],
        'existing_public_snapshot': report['existing_public_snapshot'],
    }, indent=2))


if __name__ == '__main__':
    main()
