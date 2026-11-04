from __future__ import annotations

from dataclasses import dataclass, field

from deal_common.offers import VariantOffer, discount


@dataclass
class Product:
    name: str
    url: str
    current_price: float
    original_price: float | None = None
    sizes: list[str] | None = None
    product_type: str | None = None
    image_url: str | None = None
    brand: str | None = None

    offers: list[VariantOffer] = field(default_factory=list)
    tags: tuple[str, ...] = ()

    @property
    def discount_pct(self) -> float:
        return discount(self.current_price, self.original_price)

    @property
    def savings(self) -> float:
        if self.original_price is None:
            return 0.0
        return round(self.original_price - self.current_price, 2)
