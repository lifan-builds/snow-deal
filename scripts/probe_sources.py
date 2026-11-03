"""Probe explicit candidate sources through the real catalog ingestion pipeline.

Writes isolated public-data snapshots and receipts. It never enables or deploys sources.
"""
import argparse
import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for relative in ("common", "catalogs/cycling/src", "catalogs/tools/src"):
    sys.path.insert(0, str(ROOT / relative))

from deal_common.catalog.query import query  # noqa: E402
from deal_common.catalog.refresh import refresh  # noqa: E402
from deal_common.catalog.storage import read_sources  # noqa: E402
from deal_common.config import RetailerConfig  # noqa: E402


async def probe(candidates, output, *, max_pages=12):
    from cycling_deals.catalog import CATALOG as CYCLING
    from tool_deals.catalog import CATALOG as TOOLS
    if output.exists():
        raise ValueError("Choose a new output directory to preserve previous evidence")
    output.mkdir(parents=True)
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
        filters = dict(min_reference=base.default_reference, max_price=0, min_discount=0, stock=True, page=1)
        eligible = query(sources, filters)
        deep = query(sources, {**filters, "min_discount": 40})
        report = {"candidate": candidate, "checked_at": datetime.now(timezone.utc).isoformat(),
                  "snapshot": path.name, "refresh": results[0],
                  "eligible_listings": eligible["total"], "deep_listings": deep["total"],
                  "disposition": "needs-review" if eligible["total"] else "no-eligible-complete-snapshot"}
        reports.append(report)
        (output / "report.json").write_text(json.dumps(reports, indent=2) + "\n")
        print(json.dumps({k: report[k] for k in ("candidate", "eligible_listings", "deep_listings", "disposition")}), flush=True)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pages", type=int, choices=range(1, 31), default=12)
    args = parser.parse_args()
    asyncio.run(probe(json.loads(args.manifest.read_text()), args.output, max_pages=args.max_pages))


if __name__ == "__main__":
    main()
