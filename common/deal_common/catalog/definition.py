from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from deal_common.config import RetailerConfig
from deal_common.models import Product


@dataclass(frozen=True)
class Classification:
    category: str
    format: str = ""
    platform: str = ""


@dataclass(frozen=True)
class Catalog:
    slug: str
    name: str
    eyebrow: str
    headline: str
    description: str
    categories: tuple[str, ...]
    sources: tuple[RetailerConfig, ...]
    classify: Callable[[Product], Classification | None]
    default_reference: int
    assets: Path
    art_label: str
    theme_color: str
    mark: str = "↗"
    size_label: str = "Size"
    formats: tuple[str, ...] = ()
    buying_note: str = ""
    coverage_note: str = ""
    size_option_names: tuple[str, ...] = ()
    size_value_pattern: str = ""
    brand_aliases: tuple[tuple[str, str], ...] = ()
