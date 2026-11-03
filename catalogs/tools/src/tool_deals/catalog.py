import re
from pathlib import Path

from deal_common.catalog.definition import Catalog, Classification
from deal_common.config import RetailerConfig
from deal_common.models import Product


def classify(product: Product) -> Classification | None:
    title = product.name.casefold()
    kind = (product.product_type or "").casefold()
    text = f"{title} {kind}"
    if {tag.casefold().strip().replace("_", " ") for tag in product.tags} & {
            "used", "pre-owned", "refurbished", "reconditioned", "open box", "pickup only", "in store only",
            "demo", "showroom", "display model"}:
        return None
    if re.search(r"\b(used|pre-owned|refurbished|reconditioned|recon|renewed|open.box|scratch|dent|demo|showroom|display model)\b", text):
        return None
    if re.search(r"\b(accessories|parts|rests?|jigs?(?!\s+saws?\b)|templates?|blades|bits|cutters|knives|clamps|vises|guides|gauges|books|casters|storage|staples|sawhorses|abrasives|sanding paper|batteries and chargers|apparel|fasteners|hand tools|turning tools)\b", kind):
        return None
    # Replacement parts and consumables do not become machines because their title names one.
    if re.search(r"\b(?:drill|driver|router) bits?\b", title):
        return None
    if re.search(r"\b(replacement|adapte?r|adaptor|attachment|blade(?!\s+stroke\b)|bit set|insert|filter|hose|cover|chuck|sandpaper|stand only|tool bag|rests?|jigs?(?!\s+saw\b)|templates?|stop collar|drilling guide)\b", title):
        return None
    if re.search(r"\b(cutter sets?|shaper cutters?|depth stops?|drill guides?|sharpening station|saw indicator|clamp kit|stand kit|vac switch|tool cabinet|machine cabinet|outfeed table|work station|pole saw|staples|how to|driver kit for|hole saw|casters?|systainer|sawhorse|router table system)\b", title):
        return None
    if re.search(r"\b(?:planer|jointer)\s*(?:&\s*(?:planer|jointer))?\s+knives\b", title):
        return None
    if (re.search(r"\b(band saw|bandsaw)\b", text) and re.search(r"\b(cordless|portable|20v|m18|m12)\b", text)
            or re.search(r"\b(hand|handheld|cordless) planer\b", text)
            or (re.search(r"\bplaner\b", text) and re.search(r"\bcordless\b", title))):
        category = "Power tools"
    elif re.search(r"\b(table saw|band saw|bandsaw|drill press|lathes?|planer|jointer|dust collector|dust extractor|dust processor|air compressor|benchtop|stationary|cabinet saw|cnc (?:machine|router|mill)|milling machine|mortiser|mortising machine|wide[- ]belt sander|industrial.*(?:sander|buffer|finishing machine)|scroll saw|shaper)\b", text):
        category = "Workshop equipment"
    elif re.search(r"\b(combo|combination)\b.*\bkit\b|\b\d+[- ]tool\b.*\bkit\b", title):
        category = "Combo kits"
    elif (re.search(r"\b(drill|driver|impact wrench|saw|jigsaws?|oscillating (?:multi[- ]?)?tools?|grinder|sander|router|nailer|stapler|polisher|rotary hammer|demolition hammer|vacuum|vac)\b", text)
          or (re.search(r"\bratchets?\b", text) and re.search(r"\b(cordless|pneumatic|electric)\b", text))):
        category = "Power tools"
    else:
        return None
    if re.search(r"\b(bare tool|tool.only)\b", title):
        form = "Bare tool"
    elif re.search(r"\bkit\b", title):
        form = "Kit"
    else:
        form = "Not specified"
    # Only explicit platform names from this listing; voltage alone is not compatibility.
    platform = ""
    for pattern, label in ((r"\bm18\b", "Milwaukee M18"), (r"\bm12\b", "Milwaukee M12"),
                           (r"\bflexvolt\b", "DeWalt FLEXVOLT"), (r"\b20v\s*max\b", "DeWalt 20V MAX"),
                           (r"\bxgt\b", "Makita XGT"), (r"\blxt\b", "Makita LXT")):
        brand = label.split()[0].casefold()
        if brand in f"{product.brand or ''} {title}".casefold() and re.search(pattern, title):
            platform = label
            break
    return Classification(category, form, platform)


CATALOG = Catalog(
    slug="tools", name="Bench Drop", eyebrow="THE WORKSHOP DEAL INDEX",
    headline="Build more.\nSpend less.",
    description="Deep cuts on power tools, serious kits, and workshop equipment. Ranked by percentage off, with the package details kept in view.",
    categories=("Power tools", "Combo kits", "Workshop equipment"),
    sources=(RetailerConfig(name="Tool Nut", domain="www.toolnut.com",
                            scrape_urls=["https://www.toolnut.com/collections/saws?currency=USD",
                                         "https://www.toolnut.com/collections/power-tools?currency=USD",
                                         "https://www.toolnut.com/collections/stationary-tools?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Woodcraft", domain="www.woodcraft.com",
                            scrape_urls=["https://www.woodcraft.com/collections/clearance?currency=USD",
                                         "https://www.woodcraft.com/collections/power-tools?currency=USD",
                                         "https://www.woodcraft.com/collections/woodworking-machines?currency=USD",
                                         "https://www.woodcraft.com/collections/power-tool-deals?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Craft Supplies USA", domain="woodturnerscatalog.com",
                            scrape_urls=["https://woodturnerscatalog.com/collections/wood-lathes?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Harvey Woodworking", domain="www.harveywoodworking.com",
                            scrape_urls=["https://www.harveywoodworking.com/collections/all?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="WEN", domain="wenproducts.com",
                            scrape_urls=["https://wenproducts.com/collections/power-tools?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Factory Direct Supply", domain="factorydirectsupply.com",
                            scrape_urls=["https://factorydirectsupply.com/collections/power-tools?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Grizzly Industrial", domain="www.grizzly.com", parser_type="grizzly",
                            scrape_urls=["https://www.grizzly.com/outlet-specials/shop-all"]),
             RetailerConfig(name="Max Warehouse", domain="www.maxwarehouse.com",
                            scrape_urls=["https://www.maxwarehouse.com/collections/power-tools?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="OakTree Supply", domain="www.oaktreesupply.com",
                            scrape_urls=["https://www.oaktreesupply.com/collections/clearance?currency=USD",
                                         "https://www.oaktreesupply.com/collections/jpw-overstock-items-2026?currency=USD",
                                         "https://www.oaktreesupply.com/collections/jet-and-powermatic-price-drops?currency=USD",
                                         "https://www.oaktreesupply.com/collections/scm-sale?currency=USD",
                                         "https://www.oaktreesupply.com/collections/sawstop?currency=USD"],
                            verify_shopify_currency=True),
             RetailerConfig(name="Taylor Toolworks", domain="taytools.com", parser_type="taylor",
                            scrape_urls=["https://taytools.com/power-tools?ppg=65535&pn=1"]),
             # The merchant's public product backend redirects exact variants to its current storefront.
             RetailerConfig(name="Fasteners Inc", domain="fastenersinc.myshopify.com",
                            scrape_urls=["https://fastenersinc.myshopify.com/collections/power-tools?currency=USD",
                                         "https://fastenersinc.myshopify.com/collections/power-tools-1?currency=USD",
                                         "https://fastenersinc.myshopify.com/collections/machine-tools?currency=USD",
                                         "https://fastenersinc.myshopify.com/collections/power-tool-closeouts?currency=USD",
                                         "https://fastenersinc.myshopify.com/collections/all-closeouts?currency=USD"],
                            verify_shopify_currency=True)),
    classify=classify, default_reference=200,
    assets=Path(__file__).parent / "static", art_label="02 / THE NEXT PROJECT", theme_color="#282922", mark="↘",
    formats=("Bare tool", "Kit", "Not specified"),
    brand_aliases=(("sawstop", "SawStop"), ("jet", "JET"), ("jet tools", "JET"),
                   ("kreg tool", "Kreg"), ("kreg", "Kreg"), ("dewalt", "DeWalt")),
    buying_note="A bare tool does not include a battery or charger. A kit label does not guarantee particular contents. Confirm the package, battery compatibility, shipping, and return policy on the retailer page. Check required voltage and phase for workshop machines. Clearance may be final sale.",
)
