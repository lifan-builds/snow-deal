"""Choose one eligible offer per listing before counts, order, and pagination."""
from datetime import UTC, datetime, timedelta
from math import ceil

from deal_common.catalog.identity import manufacturer_name
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


def query(sources: list[dict], filters: dict, *, now: datetime | None = None,
          brand_aliases: tuple[tuple[str, str], ...] = ()) -> dict:
    now = now or datetime.now(UTC)
    requested_brand = filters.get("brand")
    if requested_brand and brand_aliases:
        requested_brand = manufacturer_name(requested_brand, brand_aliases=brand_aliases)
    cards = []
    facets = {key: set() for key in ("brand", "store", "size", "platform")}
    fresh_sources = 0
    for source in sources:
        if not is_fresh(source["successful_at"], now):
            continue
        fresh_sources += 1
        for product in source["products"]:
            brand = (manufacturer_name(product["brand"], brand_aliases=brand_aliases)
                     if brand_aliases else product["brand"])
            facets["brand"].add(brand)
            facets["store"].add(source["name"])
            if product["platform"]:
                facets["platform"].add(product["platform"])
            for offer in product["offers"]:
                if offer["size"] and offer["availability"] == "in_stock":
                    facets["size"].add(offer["size"])
            if requested_brand and requested_brand != brand:
                continue
            if any(filters.get(key) and filters[key] != product[key]
                   for key in ("category", "format", "platform")):
                continue
            if filters.get("store") and filters["store"] != source["name"]:
                continue
            if filters.get("q"):
                search_texts = (product["name"] + " " + product["brand"], product["name"] + " " + brand)
                if not any(filters["q"].casefold() in text.casefold() for text in search_texts):
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
            cards.append({**product, "brand": brand, "offer": best, "store": source["name"],
                          "observed_at": source["successful_at"], "matching_variants": len(eligible)})
    # Keep one existing label for each match the current size_key already defines.
    size_labels = {}
    for label in sorted(facets["size"], key=lambda value: (len(value), value.casefold(), value)):
        size_labels.setdefault(size_key(label), label)
    facets["size"] = set(size_labels.values())
    cards.sort(key=lambda p: (-p["offer"]["discount"], -p["offer"]["savings"], p["name"], p["url"]))
    total = len(cards)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = min(filters["page"], pages)
    return {"cards": cards[(page - 1) * PAGE_SIZE:page * PAGE_SIZE], "total": total,
            "page": page, "pages": pages, "fresh_sources": fresh_sources,
            "facets": {key: sorted(values) for key, values in facets.items()},
            "top_discount": cards[0]["offer"]["discount"] if cards else 0}
