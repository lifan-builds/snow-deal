"""Audit and repair a COPY of a public deal snapshot; never refresh prices.

Metadata is keyed by exact product URL and must carry the stored title in `name`.
No network requests, credentials, or auth databases are used by this command.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'aggregator')]
from aggregator.db import init_db, repair_deal_categories
from aggregator.reviews import _normalize_brand, compute_and_store_deal_reviews
from snow_deals.parsers.shopify import product_type_from_item


def audit(source: Path, destination: Path, metadata: dict, report_dir: Path) -> dict:
    if source.resolve() == destination.resolve() or destination.exists():
        raise ValueError('Use a new output path; the source snapshot is never modified.')
    with sqlite3.connect(f'{source.resolve().as_uri()}?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        before = {r['id']: dict(r) for r in db.execute('SELECT * FROM deals')}
        history = db.execute('SELECT * FROM price_history ORDER BY url, observed_at').fetchall()
    shutil.copyfile(source, destination)
    asyncio.run(init_db(destination))
    matched_ids = set()
    with sqlite3.connect(destination) as db:
        for row in before.values():
            evidence = metadata.get(row['url'])
            if not evidence or evidence.get('name') != row['name']:
                continue
            product_type = product_type_from_item(evidence)
            brand = _normalize_brand(evidence['vendor']) if evidence.get('vendor') else row['brand']
            db.execute('UPDATE deals SET product_type=?, brand=? WHERE id=?', (product_type, brand, row['id']))
            matched_ids.add(row['id'])
    corrected = asyncio.run(repair_deal_categories(destination))
    asyncio.run(compute_and_store_deal_reviews(destination))
    with sqlite3.connect(destination) as db:
        db.row_factory = sqlite3.Row
        after = {r['id']: dict(r) for r in db.execute('SELECT * FROM deals')}
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT * FROM price_history ORDER BY url, observed_at').fetchall() == history
    mutable = {'category', 'length_min', 'length_max', 'brand', 'product_type', 'exclusion_reason'}
    assert before.keys() == after.keys()
    for key, row in before.items():
        assert all(after[key][field] == value for field, value in row.items() if field not in mutable)

    latest = {}
    for row in before.values():
        latest[row['store']] = max(latest.get(row['store'], ''), row['scraped_at'])
    cutoff = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=72)).isoformat()
    records = []
    for row in after.values():
        if row['scraped_at'] != latest[row['store']] or row['scraped_at'] < cutoff:
            continue
        old = before[row['id']]
        records.append({
            'id': row['id'], 'store': row['store'], 'name': row['name'], 'url': row['url'],
            'before_category': old['category'], 'category': row['category'],
            'exclusion_reason': row['exclusion_reason'], 'product_type': row['product_type'],
            'brand': row['brand'], 'price_checked_at': row['scraped_at'],
            'metadata_source': metadata.get(row['url'], {}).get('source', '') if row['id'] in matched_ids else '',
        })
    summary = {
        'audited_at': datetime.now(timezone.utc).isoformat(),
        'current_listings_audited': len(records),
        'metadata_matches_all_rows': len(matched_ids),
        'metadata_matches_current': sum(r['id'] in matched_ids for r in records),
        'retailers_audited': len({r['store'] for r in records}),
        'generic_boots_current': sum(r['category'] == 'boots' for r in records),
        'category_changes_current': sum(r['before_category'] != r['category'] for r in records),
        'category_or_exclusion_changes_all_rows': corrected,
        'excluded_current': dict(Counter(r['exclusion_reason'] for r in records if r['exclusion_reason'])),
        'unresolved_current': sum(not r['category'] and not r['exclusion_reason'] for r in records),
        'visible_categories': dict(Counter(r['category'] or 'unknown' for r in records if not r['exclusion_reason'])),
        'price_history_and_other_fields_preserved': True,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / 'summary.json').write_text(json.dumps(summary, indent=2))
    for filename, selected in [
        ('all-items.csv', records),
        ('changes.csv', [r for r in records if r['before_category'] != r['category'] or r['exclusion_reason']]),
        ('unresolved.csv', [r for r in records if not r['category'] and not r['exclusion_reason']]),
    ]:
        with (report_dir / filename).open('w', newline='') as output:
            writer = csv.DictWriter(output, fieldnames=list(records[0]) if records else ['id'])
            writer.writeheader()
            writer.writerows(selected)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-db', type=Path, required=True)
    parser.add_argument('--output-db', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--report-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.source_db, args.output_db, json.loads(args.metadata.read_text()), args.report_dir), indent=2))
