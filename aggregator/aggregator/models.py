"""Aggregated deal model wrapping snow_deals.Product."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import datetime

from aggregator.config import STORES


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

    @property
    def affiliate_url(self) -> str:
        """Returns the affiliate URL if configured, otherwise the original URL."""
        store_config = next((s for s in STORES if s.name == self.store), None)
        if not store_config or not store_config.affiliate_network:
            return self.url
            
        if store_config.affiliate_network == "avantlink":
            # https://www.avantlink.com/click.php?tt=cl&merchant_id=[MERCHANT_ID]&website_id=[WEBSITE_ID]&url=[URL]
            website_id = "YOUR_AVANTLINK_WEBSITE_ID" # Placeholder, user needs to update
            encoded_url = urllib.parse.quote_plus(self.url)
            return f"https://www.avantlink.com/click.php?tt=cl&merchant_id={store_config.affiliate_merchant_id}&website_id={website_id}&url={encoded_url}"
            
        return self.url
