"""Canonical product metadata shared by ingestion and observation matching."""
import re


def manufacturer_name(value: str | None, *, brand_aliases: tuple[tuple[str, str], ...] = ()) -> str:
    """Reject fulfillment labels, then apply only the catalog's exact aliases."""
    name = (value or "Unspecified").strip()
    if re.fullmatch(r"in stock|out of stock|esd[:：].*", name, re.IGNORECASE):
        return "Unspecified"
    return dict(brand_aliases).get(name.casefold(), name)
