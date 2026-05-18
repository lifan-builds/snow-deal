"""Shared utilities for HTML parsers."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse


def parse_price(text: str) -> float | None:
    """Extract a numeric price from text like '$269.99', 'C$485.99', or '579.99'."""
    match = re.search(r"(?:C?\$)?([\d,]+\.?\d*)", text.strip())
    if match:
        return float(match.group(1).replace(",", ""))
    return None


PLACEHOLDER_PRODUCT_NAMES = {
    "gearhead top pick",
    "top pick",
    "product image",
    "image",
}


def product_name_from_url(url: str) -> str | None:
    """Build a readable product name from a product URL slug."""
    words = product_slug_words(url)
    if not words:
        return None
    return " ".join(words).title()


def product_slug_words(url: str) -> list[str]:
    """Return normalized words from a product URL slug."""
    if not url:
        return []

    path = unquote(urlparse(url).path)
    slug = path.rstrip("/").split("/")[-1]
    slug = re.sub(r"\.(?:html?|php)$", "", slug, flags=re.IGNORECASE)
    slug = slug.strip("-_ ")
    if not slug:
        return []

    return [w for w in re.split(r"[-_]+", slug) if w]


def clean_product_name(name: str | None, url: str = "") -> str:
    """Normalize product names and recover from known placeholder labels."""
    cleaned = re.sub(r"\s+", " ", name or "").strip()
    if cleaned.lower() in PLACEHOLDER_PRODUCT_NAMES:
        return product_name_from_url(url) or ""
    return cleaned


_GENERIC_URL_PREFIXES = {
    "products",
    "product",
    "item",
    "shop",
    "mens",
    "womens",
    "men",
    "women",
}


def prefix_brand_from_url(name: str | None, url: str) -> str:
    """Prefix a model-only name with the URL's leading brand slug when safe."""
    cleaned = clean_product_name(name, url)
    if not cleaned:
        return ""

    words = product_slug_words(url)
    while words and words[0].isdigit():
        words = words[1:]
    if len(words) < 2:
        return cleaned

    candidate = words[0].lower()
    name_lower = cleaned.lower()
    if (
        candidate in _GENERIC_URL_PREFIXES
        or not candidate.isalpha()
        or candidate in name_lower.split()
    ):
        return cleaned

    # Require overlap with the rest of the slug so collection/category URLs do not pollute names.
    rest = {w.lower() for w in words[1:] if len(w) > 2}
    name_words = set(re.findall(r"[a-z0-9]+", name_lower))
    if not rest.intersection(name_words):
        return cleaned

    return f"{candidate.title()} {cleaned}"
