"""Canonical product metadata shared by ingestion and observation matching."""
import re


def manufacturer_name(value: str | None) -> str:
    """Reject fulfillment labels without guessing a manufacturer identity."""
    name = (value or "Unspecified").strip()
    if re.fullmatch(r"in stock|out of stock|esd[:：].*", name, re.IGNORECASE):
        return "Unspecified"
    return name
