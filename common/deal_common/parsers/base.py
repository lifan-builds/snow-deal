from __future__ import annotations

from abc import ABC, abstractmethod

from deal_common.models import Product


class BaseParser(ABC):
    """Interface that every site-specific parser must implement."""

    requires_product_pages = False

    def validate_listing_response(self, html: str, page_url: str, headers: dict[str, str]) -> None:
        """Optional response metadata contract, before decoding or following pages."""

    def get_product_evidence_url(self, html: str, page_url: str) -> str | None:
        """Optional same-merchant, read-only evidence needed by a product page."""
        return None

    def parse_product_evidence(self, html: str, page_url: str, evidence: str) -> list[Product]:
        raise NotImplementedError

    def parse_product_page(self, html: str, page_url: str) -> list[Product]:
        """Resolve discovery listings to authoritative offers when opted in."""
        raise NotImplementedError

    @abstractmethod
    def parse_listing_page(self, html: str, page_url: str) -> list[Product]:
        """Extract all products from a single listing page's HTML."""

    @abstractmethod
    def get_next_page_url(self, html: str, current_url: str) -> str | None:
        """Return the URL of the next page, or None if this is the last page."""
