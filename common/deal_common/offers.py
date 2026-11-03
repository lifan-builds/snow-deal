"""Variant offer facts; an unknown stock value is never a stock confirmation."""
from dataclasses import dataclass
import math
import re


def size_key(value: str | None) -> str:
    value = re.sub(r'\s+', '', (value or '').casefold())
    value = re.sub(r'(cm|mondo)$', '', value)
    aliases = {'small': 's', 'sm': 's', 'medium': 'm', 'md': 'm', 'large': 'l', 'lg': 'l',
               'extra-large': 'xl', 'x-large': 'xl'}
    return aliases.get(value, value)


def discount(price: float, reference: float | None) -> float:
    if reference is None or not all(math.isfinite(x) for x in (price, reference)) or not 0 < price < reference:
        return 0.0
    return round(100 * (1 - price / reference), 1)


@dataclass
class VariantOffer:
    variant_key: str
    url: str
    current_price: float
    original_price: float
    size: str | None = None
    options: str = ''
    availability: str = 'unknown'
    image_url: str | None = None
    reference_basis: str = 'retailer_compare_at'
    availability_note: str = ''

    @property
    def discount_pct(self) -> float:
        return discount(self.current_price, self.original_price)
