"""Keyword-based product categorization."""

from __future__ import annotations

from aggregator.config import CATEGORY_RULES


def categorize(name: str, url: str = "") -> str | None:
    """Return the best-matching category for a product name/URL, or None."""
    text = f"{name} {url}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return category
    return None
