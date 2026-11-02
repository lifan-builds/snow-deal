"""Keyword-based product categorization."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urlparse

from aggregator.config import (
    CATEGORY_RULES, EXCLUDE_KEYWORDS, NOT_HARDGOODS_KEYWORDS,
    SKI_BOOT_BRANDS, SNOWBOARD_BOOT_BRANDS,
    SKI_MODEL_NAMES, BOOT_MODEL_NAMES, SNOWBOARD_MODEL_NAMES,
    SKI_BOOT_MODEL_NAMES, SNOWBOARD_BOOT_MODEL_NAMES,
    GOGGLE_MODEL_NAMES, BINDING_MODEL_NAMES,
    MULTI_WORD_MODEL_NAMES,
)

_EXCLUSION_PATTERNS = [
    (kw.strip(), re.compile(r"\b" + re.escape(re.sub(r"[-_/]+", " ", kw).strip()) + r"(?:s)?\b"))
    for kw in EXCLUDE_KEYWORDS
]
_CATEGORY_PATTERNS = [
    (category, re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(kw.strip()) for kw in keywords) + r")(?![a-z0-9])"))
    for category, keywords in CATEGORY_RULES
]
_NOT_HARDGOODS_PATTERN = re.compile(r"\b(?:" + "|".join(re.escape(kw.strip()) for kw in NOT_HARDGOODS_KEYWORDS) + r")\b")


def explicit_non_equipment_category(name: str) -> str | None:
    """Recognize clear product nouns before boot/model keywords.

    Title-only evidence also allows safe corrections to stored listings whose
    original retailer product type is no longer available.
    """
    text = re.sub(r"[-_/]+", " ", unescape(name).lower())
    if re.search(r"\bbody glove\b", text):
        return None  # Brand name, not a glove product noun.
    if re.search(r"\b(?:gloves?|mittens?|mitts?)\b", text):
        return "gloves"
    if (re.search(r"\bbalaclava\b", text)
            and re.search(r"\b(?:hoodies?|hoody|pullover)\b", text)):
        return "layers"  # Includes tops with an integrated balaclava.
    if re.search(r"\b(?:bags?|beanies?|balaclavas?|clava|scarves|scarf|socks?|ski straps?)\b", text):
        return "accessories"
    # A replacement lens is not a whole goggle. Bundled bonus lenses stay goggles.
    if re.search(r"\b(?:replacement|replaement|repl|rep) lens(?:es)?\b", text):
        return "accessories"
    if re.search(r"\b(?:pole baskets?|boot dryers?|insoles?|outsoles?)\b", text):
        return "accessories"
    if re.search(r"\b(?:backpacks?|boot (?:pack|locker|caps?)|footbeds?|helmet covers?|hardshell helmet top|hardshell top helmet|ski (?:leash|lock)|snowboard leash|climbing skins?|splitboard skins?|tip loop|spare parts|universal dis[ck]|heat elements|skicase|freeride spacer|alpine sole|toe warmers?|crampons?|snowshoes?|suspenders|cable lock|torque driver)\b", text):
        return "accessories"
    if re.search(r"\b(?:skins|tool|straps|headwear|neckwear|earband|ubertube|hijab|sox)\b", text) and not re.search(r"\b(?:sno skins|shirt|ski\b|skis\b)\b", text):
        return 'accessories'
    if re.search(r"\bliners?\b", text) and not re.search(r"\bboots?\b", text):
        return "accessories"
    if re.search(r"\b(?:marker alu pro plate|marker wc pc interface|storm.*(?:spray|care kit)|montana splitclamp)\b", text):
        return 'accessories'
    if re.search(r"\b(?:pants?|bibs?|sweatpants?)\b", text):
        return "pants"
    if re.search(r"\b(?:jackets?|parkas?|anoraks?|coats?)\b", text):
        return "jackets"
    if re.search(r"\b(?:capilene|baselayers?|base layers?|midlayers?|mid layers?|fleece|hoodies?|hoody|sweatshirts?|crewneck|crew neck|leggings?)\b", text):
        return "layers"
    if re.search(r"\b(?:zip top|thermal (?:crew|top)|rollneck|t neck|lifa active crew|peachskin crew)\b", text):
        return "layers"
    if re.search(r'\b(?:crew top|lounge top|funnel neck top|knit top|sherpa|moonridge crew|dayshift crew|conduit crew)\b', text):
        return 'layers'
    if re.search(r'\b(?:poncho|shawl|knit wrap|fur collar)\b', text):
        return 'accessories'
    if re.search(r"\b(?:snowsuit|snow suit|ski suit|beast suit|murphy suit|absolute zero suit)\b", text):
        return "jackets"
    if re.search(r"\b(?:gaitor|necktube|neckband|earwarmers?|earband|airhood|wristguard|skin skins|ski skins|snowboard skins)\b", text):
        return "accessories"
    return None


def category_from_product_type(product_type: str) -> str | None:
    """Interpret retailer taxonomy before ambiguous model and collection words."""
    text = re.sub(r"[-_/]+", " ", unescape(product_type).lower()).replace('skiboots', 'ski boots')
    if not text:
        return None
    if re.search(r" - (?:ski )?poles$", product_type.lower()):
        return 'poles'
    if re.search(r'\b(?:goggles|helmets)\b', text) and not re.search(r'\b(?:lens|lenses|bags?|covers?|parts)\b', text):
        return 'helmets' if 'helmet' in text else 'goggles'
    # Retailers sometimes concatenate parents: "Ski Poles - Bindings - Binding".
    if re.search(r"\b(?:accessor(?:y|ies)|skins|tuning|headwear|neckwear|socks?|headbands?|beanies?|travel|snow safety|bags?|packs?|hats|belts|suspenders|tools|parts|scrapers)\b", text):
        return "accessories"
    if 'winter boot' in text or 'snow boot' in text:
        return 'winter boots'
    if re.search(r"\b(?:layers?|base ?layers?|mid ?layers?|sweaters?|fleece|vests?|pullovers?)\b", text):
        return 'layers'
    if re.search(r"\b(?:sweatshirts?|hoodies?|flannels?|long sleeves?|technical tops|baselayer tops)\b", text):
        return 'layers'
    if 'protective equipment' in text:
        return 'accessories'
    for category, pattern in _CATEGORY_PATTERNS:
        if category in {'pants', 'jackets', 'gloves'} and pattern.search(text):
            return category
    if re.search(r"\bboots?\b", text):
        if 'snowboard' in text:
            return 'snowboard boots'
        if re.search(r"\b(?:ski|alpine|nordic|cross country|at)\b", text):
            return 'ski boots'
        return 'boots'
    if re.search(r"\bbindings?\b", text):
        return 'bindings'
    if re.search(r"\bpoles?\b", text):
        return 'poles'
    for category, pattern in _CATEGORY_PATTERNS:
        if category in {'helmets', 'goggles', 'snowboards', 'skis'} and pattern.search(text):
            return category
    if re.search(r"\bskiing\b", text):
        return 'skis'
    return None


def _url_path(url: str) -> str:
    """Extract just the path from a URL, ignoring the domain.

    This prevents store domains like 'skiisandbiikes.com' or 'skipro.com'
    from falsely matching the 'ski' keyword.
    """
    if not url:
        return ""
    try:
        return urlparse(url).path
    except Exception:
        return url


def is_excluded(name: str, url: str = "") -> bool:
    """Return True if the product is a non-snow-sport item that should be excluded."""
    # Prepend a space so space-prefixed keywords like " used " match at start of string too
    text = " " + re.sub(r"[-_/]+", " ", f"{name} {_url_path(url)}".lower()) + " "
    if re.search(r'\b(?:shoes?|trunks?|cami|clutch|hand torch|running belt|run belt|run laces|sportswear|cover up|singlet)\b', text):
        return True
    if re.search(r'\bshort\s*(?:\((?:men|women)|(?:men|women)|20\d\d|$)', name.lower().strip()):
        return True
    if re.search(r'\b(?:nanogrip|seaglass bay|sunrise slider|sunamee|bell sanction|enduro (?:pro )?(?:elbow|knee))\b', text):
        return True
    if re.search(r'\b(?:hiking boot|boxers?|awning|freedom slides|reef one slide|little rio slide|puffy slide|sport flex slide)\b', text):
        return True
    for kw, pattern in _EXCLUSION_PATTERNS:
        # These brands also make genuine snowboard boots.
        if kw in {"vans", "adidas"} and re.search(r"\bsnowboard boots?\b", text):
            continue
        if pattern.search(text):
            return True
    return False


def exclusion_reason(name: str, url: str = '', product_type: str = '') -> str | None:
    text = f'{name} {product_type}'
    if re.search(r'\b(?:juniors?|jrs?|kids?|youth|toddlers?|baby|boys?|girls?|infants?|child|children|grom|teens?)\b', text, re.I):
        return 'children'
    if is_excluded(text, url):
        return 'non-snow'
    return None


def _disambiguate_boot(name: str, url: str = "") -> str:
    """Disambiguate a generic 'boots' match into 'ski boots' or 'snowboard boots'.

    Uses brand names, model names, and URL clues.
    Returns 'ski boots', 'snowboard boots', or 'boots' if uncertain.
    """
    name_lower = name.lower()
    url_lower = _url_path(url).lower()

    if re.search(r"\bscott\b.*\b(?:celeste|cosmos)\b", name_lower):
        return 'ski boots'
    if re.search(r"\b(?:union reset|northwave)\b", name_lower):
        return 'snowboard boots'
    if (re.search(r'\bsalomon\b.*\b(?:pearl|vista|x approach)\b', name_lower)
            or re.search(r'\bk2\b.*\b(?:contour|kinsley|haven|raider|holgate)\b', name_lower)):
        return 'snowboard boots'
    if re.search(r"\b(?:nordic|cross country|transnordic|combi)\b", name_lower):
        return 'ski boots'

    # URL clues
    if "snowboard" in url_lower:
        return "snowboard boots"
    if "ski-boot" in url_lower or "ski_boot" in url_lower:
        return "ski boots"

    # Strip Women's/Men's prefix and leading year for brand check
    clean = name_lower
    for prefix in ("women's ", "men's ", "womens ", "mens ", "unisex "):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            break
    parts = clean.split()
    if parts and re.match(r"^20\d{2}$", parts[0]):
        parts = parts[1:]
    first_word = parts[0] if parts else ""
    two_words = " ".join(parts[:2]) if len(parts) >= 2 else ""

    # Check brand
    if first_word in SKI_BOOT_BRANDS or two_words in SKI_BOOT_BRANDS:
        return "ski boots"
    if first_word in SNOWBOARD_BOOT_BRANDS or two_words in SNOWBOARD_BOOT_BRANDS:
        return "snowboard boots"

    # Check model names
    words = set(name_lower.split())
    if words & SKI_BOOT_MODEL_NAMES:
        return "ski boots"
    if words & SNOWBOARD_BOOT_MODEL_NAMES:
        return "snowboard boots"

    # ThirtyTwo alias
    if first_word == "32":
        return "snowboard boots"

    # Brands that make both ski and snowboard boots — check model context
    # Atomic, Salomon, K2, Head, Nordica = primarily ski boot brands
    ski_also_brands = {"atomic", "salomon", "head", "nordica", "k2", "rossignol",
                       "fischer", "volkl", "elan", "blizzard", "dynastar",
                       "dynafit", "movement", "armada"}
    # Vans, Ride, Burton, Nitro, Rome, Bataleon = primarily snowboard boot brands
    snb_also_brands = {"vans", "ride", "burton", "nitro", "rome", "bataleon"}

    if first_word in ski_also_brands:
        return "ski boots"
    if first_word in snb_also_brands:
        return "snowboard boots"

    # GW suffix = GripWalk = ski boots
    if " gw" in name_lower:
        return "ski boots"

    # BOA + touring/backcountry context = ski boots
    if "touring" in name_lower or "backcountry" in name_lower or "alpine" in name_lower:
        return "ski boots"

    return "boots"


def categorize(name: str, url: str = "", product_type: str = "", *, brand: str = "") -> str | None:
    """Return the best-matching category for a product name/URL, or None.

    Use explicit product nouns and retailer taxonomy before model inference.
    """
    if is_excluded(f"{name} {product_type}", url):
        return None
    explicit = explicit_non_equipment_category(name)
    if explicit:
        return explicit
    name = unescape(name)
    title = re.sub(r"[-_/]+", " ", name.lower())
    if re.search(r'\bski\s*\+', title):
        return 'skis'
    if re.search(r'\bsnowboards?\s*(?:\+|with\b|and\b)', title):
        return 'snowboards'
    if '+' in name and 'binding' in title and 'boot' in title:
        primary = categorize(name.split('+', 1)[0], brand=brand)
        if primary in {'skis', 'snowboards', 'ski boots', 'snowboard boots'}:
            return primary
    # The presence/order of "binding" alone does not identify the thing for sale.
    if ((re.search(r"\bskis\b", title) or re.search(r"\bski\s*(?:with\b|w\b|and\b|system\b|only\b)", title))
            and re.search(r"\bbindings?\b", title)
            and not re.search(r"\b(?:for|fits|compatible)\b.*\bskis\b", title)):
        return 'skis'
    typed = category_from_product_type(product_type)
    # Product nouns outrank a broad parent collection/type such as "Snowboards".
    for pattern, category in [
        (r'\bsnowboard boots?\b', 'snowboard boots'),
        (r'\b(?:ski|alpine|nordic|cross country) boots?\b', 'ski boots'),
        (r'\bbindings?\b', 'bindings'),
        (r'\b(?:ski|alpine|nordic) poles?\b', 'poles'),
        (r'\b(?:helmets?|mips)\b', 'helmets'),
        (r'\bgoggles?\b', 'goggles'),
    ]:
        if re.search(pattern, title):
            return category
    if typed and typed != 'boots':
        return typed
    qualified_name = name if not brand or brand.lower() in name.lower() else f'{brand} {name}'
    # A product's name outranks collection paths; "ski sale" must not turn
    # clothing into skis. Explicit retailer product types outrank URL guesses.
    for signal in (name, product_type, _url_path(url)):
        text = " " + re.sub(r"[-_/]+", " ", signal.lower()) + " "
        if re.search(r"\b(?:ski|snow|insulated|power|freedom) suit\b", text):
            return "jackets"
        for category, pattern in _CATEGORY_PATTERNS:
            if pattern.search(text):
                if category == "boots":
                    return _disambiguate_boot(qualified_name, url)
                return category

    # A manufacturer alone is not evidence of a product category.
    name_lower = qualified_name.lower()
    if _NOT_HARDGOODS_PATTERN.search(name_lower):
        return None

    # Fallback: multi-word model names (e.g., "Black Pearl", "Huck Knife")
    for phrase, cat in MULTI_WORD_MODEL_NAMES:
        if phrase in name_lower:
            return cat

    # Fallback: known single-word model names (handles cases where brand is missing or is a year)
    words = set(name_lower.split())
    if words & SKI_BOOT_MODEL_NAMES:
        return "ski boots"
    if words & SNOWBOARD_BOOT_MODEL_NAMES:
        return "snowboard boots"
    if words & BOOT_MODEL_NAMES:
        return _disambiguate_boot(name, url)
    if words & GOGGLE_MODEL_NAMES:
        return "goggles"
    if words & BINDING_MODEL_NAMES:
        return "bindings"
    if words & SKI_MODEL_NAMES:
        return "skis"
    if words & SNOWBOARD_MODEL_NAMES:
        return "snowboards"

    return None
