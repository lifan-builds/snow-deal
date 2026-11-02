"""Snow catalog deal model with store, review, and length metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from deal_common.offers import VariantOffer
from datetime import datetime


def model_year(name: str) -> int | None:
    """Read explicit title years; never infer age from price or first observation."""
    years = re.findall(r"\b(?:19|20)\d{2}\b", name)
    if years:
        return int(years[-1])
    if re.search(r"\b00\s*[-–]\s*01\b", name):
        return 2001
    return None


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
    sizes: str | None  # Comma-separated available sizes
    length_min: int | None  # Shortest length in cm (extracted from sizes)
    length_max: int | None  # Longest length in cm (extracted from sizes)
    scraped_at: datetime
    image_url: str | None = None
    brand: str | None = None
    review_score: int | None = None
    review_award: str | None = None
    review_url: str | None = None
    first_seen: str | None = None
    previous_price: float | None = None
    currency: str = "USD"
    product_type: str | None = None

    offers: list[VariantOffer] = field(default_factory=list)
    offer_url: str | None = None
    offer_options: str | None = None
    availability: str = 'unknown'
    reference_basis: str = 'retailer_reference'

    @property
    def purchase_url(self) -> str:
        return self.offer_url or self.url

    @property
    def model_label(self) -> str | None:
        if re.search(r"\b00\s*[-–]\s*01\b", self.name):
            return 'Legacy model · 00–01'
        year = model_year(self.name)
        return f'Model {year}' if year else None
