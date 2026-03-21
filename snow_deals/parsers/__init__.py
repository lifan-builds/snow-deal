from __future__ import annotations

from urllib.parse import urlparse

from snow_deals.parsers.base import BaseParser
from snow_deals.parsers.bluezone import BlueZoneParser
from snow_deals.parsers.shopify import ShopifyParser

_REGISTRY: list[tuple[str, type[BaseParser]]] = [
    ("bluezonesports.com", BlueZoneParser),
    ("aspenskiandboard.com", ShopifyParser),
]


def get_parser(url: str) -> BaseParser:
    """Resolve the appropriate parser for a given URL."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    for pattern, parser_cls in _REGISTRY:
        if pattern in domain:
            return parser_cls()
    raise ValueError(
        f"No parser registered for domain '{domain}'. "
        f"Supported domains: {[p for p, _ in _REGISTRY]}"
    )
