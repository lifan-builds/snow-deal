"""Audit top ten + twenty seeded sampled offers from an explicit public snapshot."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
for relative in ("common", "catalogs/cycling/src", "catalogs/tools/src", "catalogs/fresh-powder/src"):
    sys.path.insert(0, str(ROOT / relative))
from deal_common.catalog.audit import audit_sample, audit_summary, select_sample  # noqa: E402
from deal_common.catalog.query import query  # noqa: E402
from deal_common.catalog.storage import read_sources  # noqa: E402


def population(path, catalog):
    if catalog == "snow":
        from aggregator.config import STORES
        domains = {s.name: s.domain for s in STORES}
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("""
                WITH selected AS (
                    SELECT d.name,d.url,d.store,d.currency,d.brand,d.category,d.scraped_at,
                           o.variant_key,o.url AS purchase_url,o.current_price,o.original_price,o.size,
                           o.options,o.availability,o.discount_pct,
                           ROW_NUMBER() OVER(PARTITION BY d.url ORDER BY o.discount_pct DESC,o.current_price,o.variant_key) AS rank
                    FROM deals d JOIN deal_offers o ON d.url=o.product_url
                    WHERE d.currency='USD' AND d.category IN ('skis','snowboards','ski boots','snowboard boots','bindings')
                      AND d.exclusion_reason IS NULL AND d.scraped_at>=? AND d.scraped_at<=?
                      AND d.scraped_at=(SELECT MAX(latest.scraped_at) FROM deals latest WHERE latest.store=d.store)
                      AND o.original_price>=500 AND o.current_price>=1 AND o.discount_pct>=40 AND o.discount_pct<95
                      AND o.availability='in_stock'
                ) SELECT * FROM selected WHERE rank=1 ORDER BY discount_pct DESC,name,url
            """, ((datetime.now(timezone.utc)-timedelta(hours=24)).replace(tzinfo=None).isoformat(),
                  datetime.now(timezone.utc).replace(tzinfo=None).isoformat())).fetchall()
        cards = [{"name": r["name"], "url": r["url"], "store": r["store"], "currency": r["currency"],
                  "offer": {"variant_key": r["variant_key"], "url": r["purchase_url"], "current_price": r["current_price"],
                            "original_price": r["original_price"], "options": r["options"], "availability": r["availability"], "size": r["size"]}} for r in rows]
    else:
        if catalog == "cycling":
            from cycling_deals.catalog import CATALOG
        else:
            from tool_deals.catalog import CATALOG
        domains = {s.name: s.domain for s in CATALOG.sources}
        rows = [s for s in read_sources(path, catalog) if s["name"] in domains]
        filters = dict(min_reference=CATALOG.default_reference, max_price=0, min_discount=0, stock=True, page=1)
        first = query(rows, filters)
        cards = []
        for page in range(1, first["pages"] + 1):
            cards.extend(query(rows, {**filters, "page": page})["cards"])
    return cards, domains


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", choices=("snow", "cycling", "tools"), required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    args = parser.parse_args()
    if not args.database.is_file() or args.output.exists():
        parser.error("Input must exist and output must be new, preserving dated evidence")
    cards, domains = population(args.database, args.catalog)
    results = asyncio.run(audit_sample(select_sample(cards, args.seed), domains))
    report = {"catalog": args.catalog, "date": datetime.now(timezone.utc).isoformat(), "seed": args.seed,
              "population": len(cards), "method": "top10-plus-seeded20-merchant-product-v1", **audit_summary(results)}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    return int(not results or any(r["status"] != "match" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
