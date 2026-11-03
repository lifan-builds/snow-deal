"""Choose one eligible offer per listing before counts, order, and pagination."""
from datetime import UTC, datetime, timedelta
from math import ceil

from deal_common.offers import discount, size_key

PAGE_SIZE = 24
FRESHNESS_HOURS = 24


def is_fresh(timestamp: str | None, now: datetime) -> bool:
    if not timestamp:
        return False
    try:
        age = now - datetime.fromisoformat(timestamp)
        return timedelta(0) <= age <= timedelta(hours=FRESHNESS_HOURS)
    except (ValueError, TypeError):
        return False


def query(sources: list[dict], filters: dict, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    cards = []
    facets = {key: set() for key in ("brand", "store", "size", "platform")}
    fresh_sources = 0
    for source in sources:
        if not is_fresh(source["successful_at"], now):
            continue
        fresh_sources += 1
        for product in source["products"]:
            facets["brand"].add(product["brand"])
            facets["store"].add(source["name"])
            if product["platform"]:
                facets["platform"].add(product["platform"])
            for offer in product["offers"]:
                if offer["size"] and offer["availability"] == "in_stock":
                    facets["size"].add(offer["size"])
            if any(filters.get(key) and filters[key] != product[key]
                   for key in ("category", "brand", "format", "platform")):
                continue
            if filters.get("store") and filters["store"] != source["name"]:
                continue
            if filters.get("q") and filters["q"].casefold() not in (product["name"] + " " + product["brand"]).casefold():
                continue
            eligible = []
            for offer in product["offers"]:
                if filters.get("size") and (offer["availability"] != "in_stock"
                        or size_key(offer["size"]) != size_key(filters["size"])):
                    continue
                if filters.get("stock") and offer["availability"] != "in_stock":
                    continue
                pct = discount(offer["current_price"], offer["original_price"])
                if (pct <= 0 or offer["availability"] not in {"in_stock", "unknown"}
                        or pct < filters["min_discount"]
                        or offer["original_price"] < filters["min_reference"]
                        or (filters["max_price"] and offer["current_price"] > filters["max_price"])):
                    continue
                eligible.append({**offer, "discount": pct,
                                 "savings": round(offer["original_price"] - offer["current_price"], 2)})
            if not eligible:
                continue
            best = min(eligible, key=lambda o: (-o["discount"], -o["savings"], o["current_price"], o["variant_key"]))
            cards.append({**product, "offer": best, "store": source["name"],
                          "observed_at": source["successful_at"], "matching_variants": len(eligible)})
    cards.sort(key=lambda p: (-p["offer"]["discount"], -p["offer"]["savings"], p["name"], p["url"]))
    total = len(cards)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = min(filters["page"], pages)
    return {"cards": cards[(page - 1) * PAGE_SIZE:page * PAGE_SIZE], "total": total,
            "page": page, "pages": pages, "fresh_sources": fresh_sources,
            "facets": {key: sorted(values) for key, values in facets.items()},
            "top_discount": cards[0]["offer"]["discount"] if cards else 0}
