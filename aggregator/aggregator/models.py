"""Aggregated deal model wrapping snow_deals.Product."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AggregatedDeal:
    """A deal record enriched with store and category metadata."""

    id: int | None
    store: str
    name: str
    url: str
    current_price: float
    original_price: float | None
    discount_pct: float
    category: str | None
    image_url: str | None
    scraped_at: datetime
