"""Size parsing shared by scraping and offline snapshot repair."""
from __future__ import annotations

import re

_CM_PATTERN = re.compile(r'(?<![\d.])(\d+)\s*(?:cm|W(?:IDE)?\b)', re.IGNORECASE)


def extract_lengths(sizes_str: str | None) -> tuple[int | None, int | None]:
    """Extract min/max ski/snowboard lengths in cm from a sizes string.

    Returns (length_min, length_max) or (None, None) if no lengths found.
    Filters to plausible ski/board lengths (100-220cm).
    """
    if not sizes_str:
        return None, None
    lengths = [
        int(m) for m in _CM_PATTERN.findall(sizes_str)
        if 100 <= int(m) <= 220
    ]
    if not lengths:
        return None, None
    return min(lengths), max(lengths)

