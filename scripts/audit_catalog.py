"""Audit an explicitly named public catalog snapshot, read-only; never discover DBs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "common"))
from deal_common.catalog.query import query  # noqa: E402
from deal_common.catalog.storage import read_sources  # noqa: E402


def audit(path, catalog, floor, now):
    sources = read_sources(path, catalog)
    base = dict(min_discount=0, min_reference=floor, max_price=0, page=1, stock=True)
    initial = query(sources, base, now=now)
    cards = []
    for page in range(1, initial["pages"] + 1):
        cards.extend(query(sources, {**base, "page": page}, now=now)["cards"])
    deep = [p for p in cards if p["offer"]["discount"] >= 40]
    fresh = sum((now - datetime.fromisoformat(p["observed_at"])).total_seconds() <= 86400 for p in cards)
    return {"catalog": catalog, "measured_at": now.isoformat(), "reference_floor": floor,
            "scope": "snapshot-listed offers; not independent merchant verification or unique model count",
            "eligible_in_stock_listings": len(cards), "deep_deal_listings": len(deep),
            "useful_retailers": sorted({p["store"] for p in deep}),
            "checked_within_24h_percent": round(fresh / len(cards) * 100, 2) if cards else None,
            "exact_size_facets": initial["facets"]["size"],
            "top_offers": [{"name": p["name"], "store": p["store"], "url": p["offer"]["url"],
                            "price": p["offer"]["current_price"], "reference": p["offer"]["original_price"],
                            "discount": p["offer"]["discount"], "size": p["offer"]["size"]} for p in deep[:10]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--catalog", choices=("cycling", "tools"), required=True)
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error("Snapshot does not exist; no database will be created")
    print(json.dumps(audit(args.database, args.catalog, {"cycling": 1000, "tools": 200}[args.catalog],
                           datetime.now(timezone.utc)), indent=2))


if __name__ == "__main__":
    main()
