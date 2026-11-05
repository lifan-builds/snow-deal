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


@pytest.mark.parametrize(('title', 'kind', 'expected'), [
    ('Dakine Thrillium Bike Glove', 'Bike', None),
    ('Trail Bike Gloves with Free Mountain Bike', 'Bike', None),
    ('Road Bike Jersey', 'Bicycles', None),
    ('Commuter Electric Bike with Gloves and Lights', 'Electric Bikes', 'Electric bikes'),
    ('Road Bike w/ Rack and Jersey', 'Road Bikes', 'Road bikes'),
    ('Road Bike w/Gloves', 'Road Bikes', 'Road bikes'),
    ('Bike Gloves w/Road Bike', 'Bike', None),
    ('Mountain Bike Including Gloves', 'Mountain Bikes', 'Mountain bikes'),
    ('Road Bike with Carbon Frame', 'Road Bikes', 'Road bikes'),
    ('Carbon Frame Mountain Bike', 'Mountain Bikes', 'Mountain bikes'),
    ('Carbon Frameset with Fork', 'Frameset', 'Framesets'),
    ('Road Bike with Used Light', 'Road Bikes', None),
    ('Bike Glove', 'Mountain Frame', None),
    ('Carbon Frameset', 'Frame Parts', None),
    ('Mountain Bike', 'Bike Gloves', None),
])
def test_primary_apparel_and_included_accessories_respect_equipment_identity(title, kind, expected):
    result = classify(Product(title, 'https://example.com/products/item', 500, 2000, product_type=kind))
    assert (result.category if result else None) == expected


@pytest.mark.parametrize('kind', [
    'Mountain Frame', 'Mountain Frames', 'Road Frame', 'All-Road Frame',
    'BMX Frame', 'Fat Bike Frame', 'Mountain E-Bike Frame', 'Gravel & Cyclocross Frames',
])
def test_explicit_observed_bicycle_frame_taxonomies_are_framesets(kind):
    product = Product('2025 Mondraker FOXY CARBON RR 29 inch Enduro/Am Mountain Bike',
                      'https://example.com/products/frame', 1950, 3800, product_type=kind)
    assert classify(product).category == 'Framesets'


@pytest.mark.parametrize('kind', ['Frame Parts', 'Bike Frame Pump', 'Suspension Forks', 'Picture Frame'])
def test_frame_taxonomy_matching_does_not_override_accessories_or_unrelated_frames(kind):
    product = Product('Component', 'https://example.com/products/component', 500, 1000, product_type=kind)
    assert classify(product) is None


def test_category_corrections_preserve_exact_offers_through_normalization_and_query():
    from copy import deepcopy
    from datetime import UTC, datetime

    from cycling_deals.catalog import CATALOG
    from deal_common.catalog.query import query
    from deal_common.catalog.refresh import normalize
    from deal_common.offers import VariantOffer

    def item(handle, title, kind, key, price, reference, *, stock='in_stock'):
        url = 'https://example.com/products/' + handle
        return Product(title, url, price, reference, product_type=kind, brand='Manufacturer',
                       offers=[VariantOffer(key, url + '?variant=' + key, price, reference,
                                            size='MD', options='Medium / Blue', availability=stock)])

    frame = item('frame', '2025 Mountain Bike', 'Mountain Frame', 'frame-md', 1950, 3800)
    frame.offers.append(VariantOffer('delayed-xl', frame.url + '?variant=delayed-xl', 1500, 3800,
                                    size='XL', options='Extra Large / Red', availability='unknown'))
    bike = item('bike', 'Mountain Bike with Carbon Frame', 'Mountain Bikes', 'bike-md', 2000, 4000)
    glove = item('glove', 'Dakine Thrillium Bike Glove', 'Bike', 'glove-md', 20, 50)
    raw = [frame, bike, glove]
    original = deepcopy(raw)
    normalized = normalize(raw, CATALOG, 'example.com')
    assert raw == original
    assert [row['name'] for row in normalized] == [frame.name, bike.name]
    assert [row['category'] for row in normalized] == ['Framesets', 'Mountain bikes']
    source = {'name': 'Fixture', 'successful_at': datetime.now(UTC).isoformat(), 'products': normalized}
    filters = {'min_reference': 0, 'max_price': 0, 'min_discount': 0, 'stock': True,
               'category': 'Framesets', 'size': 'Medium', 'page': 1}
    result = query([source], filters)
    assert result['total'] == 1 and len(result['cards']) == 1
    selected = result['cards'][0]
    assert selected['name'] == frame.name
    assert (selected['offer']['variant_key'], selected['offer']['size'], selected['offer']['options']) == (
        'frame-md', 'MD', 'Medium / Blue')
    assert (selected['offer']['current_price'], selected['offer']['original_price']) == (1950, 3800)
    assert selected['offer']['url'] == frame.offers[0].url
    assert selected['offer']['availability'] == 'in_stock'
    assert query([source], {**filters, 'size': 'XL'})['total'] == 0
    assert query([source], {**filters, 'category': '', 'size': ''})['total'] == 2
