"""Probe explicit candidate sources through the real catalog ingestion pipeline.

Writes isolated public-data snapshots and receipts. It never enables or deploys sources.
"""
import argparse
import asyncio
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for relative in ("common", "catalogs/cycling/src", "catalogs/tools/src"):
    sys.path.insert(0, str(ROOT / relative))

from deal_common.catalog.audit import audit_sample, audit_summary, select_sample
from deal_common.catalog.query import query
from deal_common.catalog.refresh import refresh
from deal_common.catalog.storage import read_sources
from deal_common.config import RetailerConfig


def all_cards(sources, filters):
    first = query(sources, filters)
    cards = list(first['cards'])
    for page in range(2, first['pages'] + 1):
        cards.extend(query(sources, {**filters, 'page': page})['cards'])
    return cards


def merchant_selection(sources, filters, seed):
    cards = all_cards(sources, filters)
    fixed = select_sample(cards, seed)
    # Keep the established one-selected-offer-per-listing population and fixed
    # sample. Supplemental coverage includes every deep listing in that population.
    deep = [card for card in cards if card['offer']['discount'] >= 40]
    selected = {}
    for card in fixed + deep:
        key = (card['store'], card['url'], card['offer']['variant_key'], card['offer']['url'])
        selected.setdefault(key, card)
    return list(selected.values()), len(cards), len(fixed), len(deep)


async def candidate_audit(sources, filters, config, refresh_result, *, seed):
    selected, population, fixed_count, deep_count = merchant_selection(sources, filters, seed)
    complete = refresh_result['status'] == 'complete' and not refresh_result.get('errors')
    results = await audit_sample(selected, {config.name: config.domain}, delay=2) if complete and selected else []
    passed = complete and bool(selected) and len(results) == len(selected) and all(
        result['status'] == 'match' for result in results)
    report = {'source': config.name, 'date': datetime.now(UTC).isoformat(), 'seed': seed,
              'method': 'top10-plus-seeded20-plus-all-deep-listings-v1',
              'population': population, 'fixed_sample_size': fixed_count,
              'deep_selected_listings': deep_count, 'selected_offers': len(selected),
              'refresh_complete': complete, 'passed': passed, **audit_summary(results)}
    if not complete:
        report['reason'] = 'Source refresh incomplete; merchant audit was not started'
    elif not selected:
        report['reason'] = 'No eligible fresh in-stock offers to audit'
    return report


async def probe(candidates, output, *, max_pages=12, audit_merchants=False, seed=None):
    from cycling_deals.catalog import CATALOG as CYCLING
    from tool_deals.catalog import CATALOG as TOOLS
    if output.exists():
        raise ValueError("Choose a new output directory to preserve previous evidence")
    output.mkdir(parents=True)
    if seed is None:
        seed = int(datetime.now(UTC).strftime('%Y%m%d'))
    reports = []
    # Sequential sources avoid accidental same-domain concurrency across aliases.
    for index, candidate in enumerate(candidates):
        base = {"cycling": CYCLING, "tools": TOOLS}[candidate["catalog"]]
        config = RetailerConfig(name=candidate["name"], domain=candidate["domain"],
                                parser_type=candidate.get("parser_type", "shopify"),
                                scrape_urls=candidate["scrape_urls"], verify_shopify_currency=True)
        catalog = replace(base, sources=(config,))
        path = output / f"{index:02d}-{base.slug}.db"
        results = await refresh(catalog, path, max_pages=max_pages, delay=2)
        sources = read_sources(path, base.slug)
        filters = {"min_reference": base.default_reference, "max_price": 0, "min_discount": 0, "stock": True, "page": 1}
        eligible = query(sources, filters)
        deep = query(sources, {**filters, "min_discount": 40})
        report = {"candidate": candidate, "checked_at": datetime.now(UTC).isoformat(),
                  "snapshot": path.name, "refresh": results[0],
                  "eligible_listings": eligible["total"], "deep_listings": deep["total"],
                  "disposition": "needs-review" if eligible["total"] else "no-eligible-complete-snapshot"}
        if audit_merchants:
            receipt = await candidate_audit(sources, filters, config, results[0], seed=seed)
            filename = f'{index:02d}-{base.slug}-merchant-audit.json'
            (output / filename).write_text(json.dumps(receipt, indent=2) + '\n')
            report['merchant_audit'] = {'receipt': filename, 'passed': receipt['passed'],
                                        'sample_size': receipt['sample_size']}
            report['disposition'] = ('merchant-audited-needs-review' if receipt['passed']
                                     else 'merchant-audit-failed')
        reports.append(report)
        (output / "report.json").write_text(json.dumps(reports, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ("candidate", "eligible_listings", "deep_listings", "disposition")}), flush=True)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pages", type=int, choices=range(1, 31), default=12)
    parser.add_argument('--audit-merchants', action='store_true',
                        help='Audit the fixed sample and every deep selected listing after a complete refresh')
    parser.add_argument('--seed', type=int, help='Fixed merchant sample seed; defaults to the current UTC date')
    args = parser.parse_args()
    reports = asyncio.run(probe(json.loads(args.manifest.read_text()), args.output, max_pages=args.max_pages,
                               audit_merchants=args.audit_merchants, seed=args.seed))
    return int(args.audit_merchants and (not reports or any(
        not report['merchant_audit']['passed'] for report in reports)))


if __name__ == "__main__":
    raise SystemExit(main())
