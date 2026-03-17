from __future__ import annotations

from abc import ABC, abstractmethod

from deal.models import Product


class BaseParser(ABC):
    """Interface that every site-specific parser must implement."""

    @abstractmethod
    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        """Extract all products from a single listing page's HTML."""

    @abstractmethod
    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        """Return the URL of the next page, or None if this is the last page."""
