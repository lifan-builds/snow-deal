"""Decode observed Harvey shipping notices without equating orders with stock."""
import re
import unicodedata
from urllib.parse import urlsplit


def shipping_notice(item: dict, variant: dict, url: str) -> str:
    """Return an unresolved shipping notice for the affected exact variant.

    Harvey uses its vendor field for ESD notices, sometimes scoped to a color.
    A missing year or expired-looking date is not evidence that stock arrived.
    Ambiguous scopes conservatively apply to every variant until clarified.
    """
    if (urlsplit(url).hostname or "").removeprefix("www.") != "harveywoodworking.com":
        return ""
    vendor = unicodedata.normalize("NFKC", str(item.get("vendor") or "")).strip()
    if not re.match(r"ESD\s*:", vendor, re.IGNORECASE):
        return ""
    estimate = vendor.split(":", 1)[1].strip()
    if not estimate or len(estimate) > 160:
        return "Retailer lists an estimated shipping date; timing needs confirmation."
    note = f"Retailer shipping estimate: {estimate}"
    scoped = re.fullmatch(r"(.+?)\s*\(([^()]+)\)", estimate)
    options = item.get("options") or []
    color_positions = [i for i, option in enumerate(options)
                       if isinstance(option, dict)
                       and str(option.get("name", "")).strip().casefold() in {"color", "colour"}]
    if not scoped or len(color_positions) != 1:
        return note
    position = color_positions[0]

    def color(candidate):
        value = candidate.get(f"option{position + 1}")
        if value is None:
            values = candidate.get("options") or []
            value = values[position] if isinstance(values, list) and len(values) > position else None
        return unicodedata.normalize("NFKC", str(value or "")).strip()

    scope = scoped[2].strip()
    pattern = re.compile(r"(?<!\w)" + re.escape(scope) + r"(?!\w)", re.IGNORECASE)
    variants = item.get("variants") or []
    # Never silently clear a notice whose qualifier cannot be bound to a color.
    if not scope or not any(isinstance(v, dict) and pattern.search(color(v)) for v in variants):
        return note
    selected = color(variant)
    return note if not selected or pattern.search(selected) else ""
