"""Retailer connection settings, independent of any product taxonomy."""

from dataclasses import dataclass, field


@dataclass
class RetailerConfig:
    """Configuration for a single retailer."""

    name: str
    domain: str
    scrape_urls: list[str] = field(default_factory=list)
    parser_type: str = "shopify"
    use_browser: bool = False  # True = use Playwright headless browser
    currency: str = "USD"   # Price currency (USD or CAD)
    shopify_products_limit: int = 250  # Lower for stores whose JSON feed fails at 250

    verify_shopify_currency: bool = False

    # Affiliate tracking
    affiliate_network: str | None = None  # e.g., "avantlink", "impact", "skimlinks"
    affiliate_merchant_id: str | None = None  # e.g., "12345"
