import pytest

from cycling_deals.catalog import classify
from deal_common.models import Product


@pytest.mark.parametrize("name,kind,expected", [
    ("Carbon Road Bike", "Road Bikes", "Road bikes"),
    ("Carbon Frameset", "Framesets", "Framesets"),
    ("Trail E-Mountain Bike", "Bikes", "Electric bikes"),
    ("Gravel Bike", "Gravel Bikes", "Gravel bikes"),
    ("Carbon Road Bike Helmet", "Helmets", None),
    ("Ex-Demo Mountain Bike", "Mountain Bikes", None),
    ("Kids Mountain Bike", "Bikes", None),
    ("Road Bike Rack", "", None),
    ("Siskiu D7", "Mountain Bikes", "Mountain bikes"),
    ("Eastern Alpaka - Gray", "Hardtail", "Mountain bikes"),
    ("Trail Model - Black", "Full Suspension", "Mountain bikes"),
    ("Carbon Frame - Blue", "MTB Frames", "Framesets"),
    ("Sentinel Carbon Frame", "AM/Enduro Frames", "Framesets"),
    ("Turbo Vado 4.0", "E-Commuter", "Electric bikes"),
    ("Frame Protection", "Frame Accessories", None),
    ("Bike Pants", "Bike Pants", None),
    ("Merino Bike Socks", "Bike Socks", None),
    ("38c Tire (Black)", "Bicycles", None),
    ("Surly Moonlander Fat Tire Bike Frameset", "MTB Frames", "Framesets"),
    ("29.8mm Seat Post Clamp", "Bicycles", None),
    ("Returned / Unridden Gravel Bike", "Bicycles", None),
    ("Pivot Firebird Blemish", "Mountain Bikes", None),
    ("Pivot Shuttle BLEM", "Electric Bikes", None),
    ("Display Trail Model", "Display Mountain Bikes", None),
    ("Rhinodillos Tire Liner", "Bike Maintenance", None),
    ("Kryptonite Krytoflex Cable", "Bike Lock", None),
    ("Fabric Mini Pump", "Bike Pumps", None),
    ("POC Ora Clarity Goggle", "Bike goggle", None),
    ("MSW Miniac GO GPS Bike Computer", "Bike Computers and Heart Rate Monitors", None),
    ("Lezyne KTV Drive Headlight and Taillight Set", "Bike Lights", None),
    ("Shimano Stainless DERAILLEUR Cable and Housing Set", "Bike Part", None),
    ("Shimano SM-MA-F180P/P2 Disc Brake Adaptor", "Bike Part", None),
    ("Commuter Electric Bike with Lights", "Electric Bikes", "Electric bikes"),
])
def test_scope(name, kind, expected):
    actual = classify(Product(name, "https://example.com", 500, 2000, product_type=kind))
    assert (actual.category if actual else None) == expected


@pytest.mark.parametrize("tag", ["used", "consignment", "pickup_only", "ebike_block_ship",
                                "in-store-only", "no-ship",
                                "condition:open-box", "condition:lightly-ridden", "condition:new-cosmetic-blem"])
def test_retailer_restrictions_survive_into_classification(tag):
    product = Product("Electric Mountain Bike", "https://example.com", 1500, 4000,
                      product_type="Bikes", tags=(tag, "ship-usa"))
    assert classify(product) is None


def test_regional_shipping_restriction_does_not_mean_no_us_shipping():
    product = Product("Electric Mountain Bike", "https://example.com", 1500, 4000,
                      product_type="Bikes", tags=("nyc_ship_block",))
    assert classify(product).category == "Electric bikes"


def test_state_bicycle_taxonomy_requires_positive_bicycle_tag():
    product = Product("6061 All-Road - Dune Tan", "https://example.com", 1195, 1399.99,
                      product_type="6061 All Road", tags=("Bicycle",), brand="State Bicycle Co.")
    assert classify(product).category == "Gravel bikes"
    product.tags = ()
    assert classify(product) is None
    product.tags = ("Bicycle",)
    product.brand = "Another Brand"
    assert classify(product) is None


def test_manufacturer_name_is_not_bicycle_product_evidence():
    product = Product("State Bicycle Co. 38c Tire (Black)", "https://example.com", 20, 30,
                      product_type="Bicycles", brand="State Bicycle Co.")
    assert classify(product) is None


@pytest.mark.parametrize('value', ['M', 'MD', 'LG', 'X-Large', 'Medium/Large', 'S3 (29)',
                                  '58CM', '20.5in', 'M #MWS Options 1', 'One Size Fits Most',
                                  '26 TALL', '49cm (19.25")', 'M (29" wheel)'])
def test_supported_frame_size_values(value):
    import re
    from cycling_deals.catalog import FRAME_SIZE_PATTERN
    assert re.fullmatch(FRAME_SIZE_PATTERN, value, re.I)


@pytest.mark.parametrize('value', ['Turquoise', 'Cobalt', 'Raw Carbon', '24" wheel',
                                  '2.5 foot SeatSaver Cable', '4 foot', '7 feet',
                                  '20 x 2.0-2.125', '26 x 2.0-2.125'])
def test_mislabeled_color_or_wheel_size_is_not_frame_size(value):
    import json
    from cycling_deals.catalog import CATALOG
    from deal_common.parsers.shopify import ShopifyParser
    parser = ShopifyParser(size_option_names=CATALOG.size_option_names,
                           size_value_pattern=CATALOG.size_value_pattern)
    data = {'products': [{'title': 'Yeti Mountain Bike', 'handle': 'yeti',
                         'options': [{'name': 'Size'}, {'name': 'Color'}],
                         'variants': [{'id': 1, 'price': '2000', 'compare_at_price': '5000',
                                       'available': True, 'option1': value, 'option2': 'Medium'}]}]}
    product = parser.parse_listing_page(json.dumps(data), 'https://shop.example/collections/sale')[0]
    assert product.offers[0].size is None
    assert product.offers[0].options == f'{value} / Medium'
    assert product.offers[0].url.endswith('variant=1')


@pytest.mark.parametrize("name,kind,brand,expected", [
    ("Rocky Mountain Solo Gravel Bike", "Gravel Bike", "Rocky Mountain", "Gravel bikes"),
    ("Rocky Mountain Road Bike", "Road Bike", "Rocky Mountain", "Road bikes"),
    ("Rocky Mountain Instinct", "Mountain Bikes", "Rocky Mountain", "Mountain bikes"),
    ("Evil Bike Co The Offering V2 Frame Only XL - Mountain Bike Frame",
     "Full Suspension Enduro Mountain Bike", "Evil Bike Co.", "Framesets"),
    ("Frame-Only Mountain Bike", "Bikes", "Example", "Framesets"),
    ("Frame Only Repair Stand", "Bike Stands", "Example", None),
])
def test_brand_and_frame_only_do_not_misclassify_bikes(name, kind, brand, expected):
    product = Product(name, "https://example.com/products/bike", 1500, 4000,
                      product_type=kind, brand=brand)
    result = classify(product)
    assert (result.category if result else None) == expected
