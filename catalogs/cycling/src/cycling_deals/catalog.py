import re
from pathlib import Path

from deal_common.catalog.definition import Catalog, Classification
from deal_common.config import RetailerConfig
from deal_common.models import Product

# Retailers occasionally swap Size and Color labels. Preserve raw options, but
# only a recognizable frame-size value can participate in the exact-fit filter.
FRAME_SIZE_PATTERN = (
    r'(?!.*\b(?:foot|feet|ft|cable)\b)(?!\d+(?:\.\d+)?\s*[x×])'
    r'(?!.*\bwheel\b$)(?:'
    r'(?:\d+(?:\.\d+)?\s*(?:cm|in|tt|\")?|S[1-6]|Size\s+\d+)'
    r'|(?:[2-6]?X{0,3}[SML]|SM|MD|LG|ML|XM|XMD|R|Regular|All)'
    r'|(?:(?:X{1,3}-)?(?:Small|Medium|Large))|One\s+Size(?:\s+Fits\s+Most)?'
    r')(?:[ /(#-].*)?'
)


def classify(product: Product) -> Classification | None:
    title = product.name.casefold()
    kind = (product.product_type or "").casefold()
    text = f"{title} {kind}"
    tags = {tag.casefold().strip().replace("_", " ") for tag in product.tags}
    if tags & {"used", "pre-owned", "demo", "consignment", "pickup only", "in store only", "ebike block ship",
               "in-store-only", "no-ship",
               "condition:lightly-ridden", "condition:new-cosmetic-blem", "condition:open-box"}:
        return None
    if re.search(r"\b(kids?|junior|youth|boys|girls|used|pre-owned|demo|display|consignment|refurbished|reconditioned|returned|unridden|blem(?:ish(?:ed)?)?|open.box|scratch|dent)\b", text):
        return None
    if re.search(r"\b(socks?|pants?|bottles?|seat posts?|seatposts?|clamps?|goggles|jackets?|shirts?)\b", text):
        return None
    # State's broad Bicycles type also includes tires; do not reject real fat-tire bikes.
    unbranded_title = title.replace(product.brand.casefold(), "") if product.brand else title
    if (kind == "bicycles" and re.search(r"\b(tires?|tyres?)\b", title)
            and not re.search(r"\b(bikes?|bicycles?|framesets?)\b", unbranded_title)):
        return None
    # Only a positive retailer bike taxonomy or an unambiguous product name qualifies.
    # A title containing "bike" alone could be a bike rack or a helmet.
    if re.search(r"\b(helmets?|jerseys?|shorts|gloves?|shoes?|racks?|bags?|wheels?|tires?|tyres?|tubes?|pedals?|saddles?|hangers?|forks?|batteries|chargers?|covers?|stands?|trainers?|parts?|accessor(?:y|ies)|maintenance|locks?|pumps?|goggles?|computers?|heart rate|lights?|cables?|brakes?|adaptors?|adapters?)\b", kind):
        return None
    if re.search(r"\b(framesets?|frame sets?|frame[- ]only)\b", text) or kind in {
            "frames", "mtb frames", "road frames", "gravel frames", "am/enduro frames", "trail/am frames", "e-bike frames"}:
        return Classification("Framesets")
    if kind == "e-commuter":
        return Classification("Electric bikes")
    if kind in {"hardtail", "full suspension"}:
        return Classification("Mountain bikes")
    if kind == "6061 all road" and "bicycle" in tags and (product.brand or "").casefold() == "state bicycle co.":
        return Classification("Gravel bikes")
    bike_type = bool(re.search(r"\b(bikes?|bicycles?)\b", kind))
    explicit = bool(re.search(r"(?:mountain|road|gravel|hybrid|commuter|electric|trail|xc|e-mountain|e-road) (?:bikes?|bicycles?)(?:\s*\[new\])?$", title))
    if not bike_type and not explicit:
        return None
    # A manufacturer such as Rocky Mountain does not define the bike category.
    category_text = f"{unbranded_title} {kind}"
    if re.search(r"\b(e-bikes?|ebikes?|electric|e-mountain|e-road|e-gravel)\b", category_text):
        return Classification("Electric bikes")
    if re.search(r"\b(mountain|mtb|trail|enduro|downhill|xc)\b", category_text):
        return Classification("Mountain bikes")
    if "gravel" in category_text:
        return Classification("Gravel bikes")
    if "road" in category_text:
        return Classification("Road bikes")
    return Classification("Other complete bikes")


CATALOG = Catalog(
    slug="cycling", name="Big Ring", eyebrow="THE CYCLING DEAL INDEX",
    headline="More bike.\nLess money.",
    description="Big discounts on complete bikes and framesets. The deepest percentage cuts come first, with the exact size and price attached.",
    categories=("Mountain bikes", "Road bikes", "Gravel bikes", "Electric bikes", "Framesets", "Other complete bikes"),
    sources=(RetailerConfig(name="Gravity Coalition", domain="gravitycoalition.com",
                            scrape_urls=["https://gravitycoalition.com/collections/all-bikes-frames?currency=USD",
                                         "https://gravitycoalition.com/collections/bike-sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Bicycle Warehouse", domain="bicyclewarehouse.com",
                            scrape_urls=["https://bicyclewarehouse.com/collections/bikes-on-sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="BikesOnline", domain="bikesonline.com",
                            scrape_urls=["https://bikesonline.com/collections/sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Mike's Bikes", domain="mikesbikes.com",
                            scrape_urls=["https://mikesbikes.com/collections/clearance-and-sale-bikes?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="ERIK’S Bike Shop", domain="www.eriksbikeshop.com",
                            scrape_urls=["https://www.eriksbikeshop.com/collections/cycling-bicycles?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Pro Bike Supply", domain="www.probikesupply.com",
                            scrape_urls=["https://www.probikesupply.com/collections/on-sale-bikes-frames?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Contender Bicycles", domain="contenderbicycles.com",
                            scrape_urls=["https://contenderbicycles.com/collections/sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Cambria Bike", domain="cambriabike.com",
                            scrape_urls=["https://cambriabike.com/collections/mtb-bikes?currency=USD",
                                         "https://cambriabike.com/collections/mtb-frames?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="INTENSE", domain="intensecycles.com",
                            scrape_urls=["https://intensecycles.com/collections/sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Bike Mart", domain="www.bikemart.com",
                            scrape_urls=["https://www.bikemart.com/collections/bikes?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="First Stop Board Barn", domain="www.firststopboardbarn.com",
                            scrape_urls=["https://www.firststopboardbarn.com/collections/blazing-summer-bike-sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Colorado Cyclist", domain="coloradocyclist.com",
                            scrape_urls=["https://coloradocyclist.com/collections/all-bikes?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Planet Cyclery", domain="planetcyclery.com",
                            scrape_urls=["https://planetcyclery.com/collections/mtb-bikes?currency=USD",
                                         "https://planetcyclery.com/collections/road-bikes?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Worldwide Cyclery", domain="worldwidecyclery.com",
                            scrape_urls=["https://worldwidecyclery.com/collections/bikes-and-frames?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="State Bicycle Co.", domain="www.statebicycle.com",
                            scrape_urls=["https://www.statebicycle.com/collections/sale?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="The Path Bike Shop", domain="www.thepathbikeshop.com",
                            scrape_urls=["https://www.thepathbikeshop.com/collections/bike-eligible-to-ship?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Fanatik Bike Co.", domain="www.fanatikbike.com",
                            scrape_urls=["https://www.fanatikbike.com/collections/on-sale-complete-bikes?currency=USD",
                                         "https://www.fanatikbike.com/collections/on-sale-frames?currency=USD",
                                         "https://www.fanatikbike.com/collections/on-sale-e-bikes?currency=USD"],
                            verify_shopify_currency=True)),
    classify=classify, default_reference=1000, size_label="Frame size",
    size_option_names=("size", "frame size", "framesize", "bike size"),
    size_value_pattern=FRAME_SIZE_PATTERN,
    brand_aliases=(("liv", "Liv"),),
    assets=Path(__file__).parent / "static", art_label="01 / THE NEXT RIDE", theme_color="#163d32",
    buying_note="Framesets are listed separately from complete bikes. Confirm geometry, components, assembly, shipping, and return terms with the retailer. Sizes are retailer labels, not a fit recommendation.",
)
