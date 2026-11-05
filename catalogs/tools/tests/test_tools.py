import pytest
from deal_common.models import Product
from tool_deals.catalog import classify


@pytest.mark.parametrize("name,kind,category,form,platform", [
    ("DeWalt 20V MAX Drill Bare Tool", "Drills", "Power tools", "Bare tool", "DeWalt 20V MAX"),
    ("Milwaukee M18 5-Tool Combo Kit", "Combo Kits", "Combo kits", "Kit", "Milwaukee M18"),
    ("Makita LXT Circular Saw Kit", "Saws", "Power tools", "Kit", "Makita LXT"),
    ("10 Inch Table Saw", "Saws", "Workshop equipment", "Not specified", ""),
    ("DeWalt 20V MAX Battery Starter Kit", "Batteries and Chargers", None, "", ""),
    ("Table Saw Replacement Blade", "Parts", None, "", ""),
    ("Reconditioned Drill", "Drills", None, "", ""),
    ("20V MAX Drill Kit", "Drills", "Power tools", "Kit", ""),
    ("Router Corner Radius Jigs/Templates - Small", "Router Jigs", None, "", ""),
    ("Nova Modular Tool Rest", "Lathe Accessories", None, "", ""),
    ("Nova Spindle Adaptor", "Lathe", None, "", ""),
    ("Drilling Guide & Stop Collar", "Drills", None, "", ""),
    ("Belt Sander", "Sanders", "Power tools", "Not specified", ""),
    ("DeWALT 20V MAX Deep Cut Band Saw, Tool Only", "Band Saw", "Power tools", "Bare tool", "DeWalt 20V MAX"),
    ("JET 18-in. Scroll Saw", "Saws", "Workshop equipment", "Not specified", ""),
    ("JET Industrial Disc Finishing Machine", "Sander", "Workshop equipment", "Not specified", ""),
    ("3-PC. Professional 10 Inch Table Saw Package", "Saw Blades > Dado Sets", None, "", ""),
    ("3-Pc. Cabinet Door Shape-Up Shaper Cutter Sets", "Shaper Cutters", None, "", ""),
    ("Carbide Tipped Planer & Jointer Knives", "Power Tools > Jointers & Planers", None, "", ""),
    ("4-Pc. Auto Dust Collection Pack with VAC Switch", "Dust Collection", None, "", ""),
    ("Adjustable Drill Depth Stops", "", None, "", ""),
    ("Universal Saw Indicator", "Measuring & Layout > Gauges", None, "", ""),
    ("Drill Press Sharpening Station", "Power Tools > Drill Presses", None, "", ""),
    ("10 Inch Cabinet Saw with Big Eye Rip Fence", "Table Saw", "Workshop equipment", "Not specified", ""),
    ("M18 Recon BL Hex Impact Driver", "Power Tools", None, "", ""),
    ("Portacube Miter Saw Work Station", "Miter Saws", None, "", ""),
    ("Bandsaw Outfeed Table", "", None, "", ""),
    ("5 Inch Gray Industrial Fixed Caster", "Casters", None, "", ""),
    ("How to Run a Lathe", "Books", None, "", ""),
    ("1 Inch Staples for Flooring Stapler", "Staples", None, "", ""),
    ("Driver Kit for G3811", "", None, "", ""),
    ("Bi-Metal Hole Saw Sets", "", None, "", ""),
    ("Benchtop Machine Cabinet", "", None, "", ""),
    ("24 Inch Wide-Belt Sander", "Sanders", "Workshop equipment", "Not specified", ""),
    ('15" Planer - 3 HP - Straight Knives', "Planers", "Workshop equipment", "Not specified", ""),
    ('JET Industrial Buffer', "Buffers", "Workshop equipment", "Not specified", ""),
    ('Milwaukee M18 FUEL Jig Saw, Tool Only', "Jig Saws", "Power tools", "Bare tool", "Milwaukee M18"),
    ('DeWalt 20V MAX XR Brushless Cordless Jigsaw', "Jig Saws", "Power tools", "Not specified", "DeWalt 20V MAX"),
    ('DeWalt 20V MAX XR Oscillating Tool Kit', "Power Tools", "Power tools", "Kit", "DeWalt 20V MAX"),
    ('Milwaukee M12 Cordless Ratchet, Tool Only', "Ratchets", "Power tools", "Bare tool", "Milwaukee M12"),
    ('Pneumatic Ratchet', "Ratchets", "Power tools", "Not specified", ""),
    ('1/2 Inch Ratchet', "Ratchets", None, "", ""),
    ('Cordless Ratchet Replacement Head', "Ratchets", None, "", ""),
    ('Jigsaw Blade Set', "Power Tools", None, "", ""),
    ('DEWALT DCS334B Cordless Jig Saw 20V Brushless 1 in Blade Stroke Length 4-Position Orbital Action',
     'Jig Saws', 'Power tools', 'Not specified', ''),
    ('Replacement Jigsaw Blade for 1 in Blade Stroke Length', 'Jig Saws', None, '', ''),
    ('Jigsaw with 1 in Blade Stroke', 'Saw Blades', None, '', ''),
    ('DEWALT DCP580B Planer Brushless Motor 20 V 3.25 in Cutting Width 15000 RPM Cordless',
     'Planers', 'Power tools', 'Not specified', ''),
    ('Cordless Planer Replacement Knives', 'Planers', None, '', ''),
    ('Oscillating Multi-Tool Blade Kit', "Power Tools", None, "", ""),
    ('Kreg Precision Router Table System', "", None, "", ""),
    ('SCM Formula Band Saw (Showroom Model)', "Machinery", None, "", ""),
    ('Display Model Table Saw', "Table Saws", None, "", ""),
    ('Demo CNC Router', "CNC Router", None, "", ""),
    ('CNC Router with Digital Display', "CNC Router", "Workshop equipment", "Not specified", ""),
    ("20V Brushless Handheld Planer - Tool Only", "Planers", "Power tools", "Bare tool", ""),
    ("Chef'n Plastic Pepper Ball Grinder", "Pepper Ball Grinder", None, "", ""),
    ("Electric Coffee Grinder", "Grinders", None, "", ""),
    ("Brushless Angle Grinder", "Grinders", "Power tools", "Not specified", ""),
    ('Milwaukee M18 FUEL 1/2-in. High Torque Impact Wrench with Friction Ring 5.0Ah Kit (2967-21B)',
     'Impact Wrench', 'Power tools', 'Kit', 'Milwaukee M18'),
    ('DEWALT, DCV501HB, Hand Vacuum, 20V, Cordless, Wet or Dry, HEPA Filtration, 21 min Runtime',
     'Filters', 'Power tools', 'Not specified', ''),
])
def test_scope_package_and_platform(name, kind, category, form, platform):
    actual = classify(Product(name, "https://example.com", 200, 500, product_type=kind))
    if category is None:
        assert actual is None
    else:
        assert (actual.category, actual.format, actual.platform) == (category, form, platform)


def test_brand_aliases_merge_only_explicit_manufacturer_names():
    from deal_common.catalog.refresh import normalize
    from deal_common.offers import VariantOffer
    from tool_deals.catalog import CATALOG
    for brand, expected in [("Sawstop", "SawStop"), ("Jet Tools", "JET"), ("Kreg Tool", "Kreg"),
                            ("Different Tools", "Different Tools"), ("In Stock", "Unspecified"),
                            ("ESD：Nov.30（Black）", "Unspecified")]:
        product = Product("Table Saw", "https://example.com/products/saw", 200, 500, brand=brand,
                          offers=[VariantOffer(variant_key="1", url="https://example.com/products/saw?variant=1",
                                               current_price=200, original_price=500, availability="in_stock")])
        assert normalize([product], CATALOG, "example.com")[0]["brand"] == expected


@pytest.mark.parametrize(('name', 'kind', 'category', 'form'), [
    ('Festool RTS 400 Orbital Sander + CT 26 EI HEPA Dust Extractor Bundle w/ Abrasives & Filter Bags RTS+CT26',
     'Power Tools', 'Workshop equipment', 'Bundle'),
    ('Fein MULTIMASTER AMM 700 MAX Black Edition 18V Cordless Oscillating Multi-Tool Bundle with 6-Piece E-Cut Blade Set 7129476109035222967010',
     'Power Tools', 'Power tools', 'Bundle'),
    ('Bosch 18V Brushless 6-1/2" Blade Right Circular Saw (Bare) GKS18V-22N',
     'Power Tools', 'Power tools', 'Not specified'),
    ('Fein MCCS14 14" Slugger Metal Cutting Chop Saw Bundle w/ Free MCBL14 Mild Steel Blade',
     'Bundles', 'Power tools', 'Bundle'),
    ('Dust Collector with Filter', 'Dust Collection', 'Workshop equipment', 'Not specified'),
    ('Table Saw with Stand', 'Table Saws', 'Workshop equipment', 'Not specified'),
    ('Dust Extractor with Filter Bags', 'Power Tools', 'Workshop equipment', 'Not specified'),
    ('Cordless Drill with Blade Kit', 'Power Tools', 'Power tools', 'Not specified'),
    ('Circular Saw with Blade Bundle', 'Power Tools', 'Power tools', 'Not specified'),
    ('Cordless Drill Kit Including Drill Bits', 'Power Tools', 'Power tools', 'Kit'),
    ('Bosch EVS Fixed-Base Router w/ Trigger Control, 2.3 HP MRF23EVS',
     'Power Tools', 'Power tools', 'Not specified'),
    ('Bosch 18V Brushless 4-1/2" Angle Grinder with Slide Switch (Bare Tool) GWS18V-8-2N',
     'Power Tools', 'Power tools', 'Bare tool'),
    ('Ionic Drive 1/4" Trim Router with 2AH Battery and Charger Kit',
     'Routers', 'Power tools', 'Kit'),
])
def test_complete_tools_keep_explicitly_included_accessories(name, kind, category, form):
    actual = classify(Product(name, 'https://example.com/products/tool', 300, 500, product_type=kind))
    assert actual is not None
    assert (actual.category, actual.format, actual.platform) == (category, form, '')


@pytest.mark.parametrize(('name', 'kind', 'tags'), [
    ('Festool Filter Bags with Free Orbital Sander', 'Power Tools', ()),
    ('Circular Saw Blade with Drill Bundle', 'Power Tools', ()),
    ('Circular Saw Blades with Drill Bundle', 'Power Tools', ()),
    ('Replacement Circular Saw with Free Blade', 'Power Tools', ()),
    ('6-Piece Blade Set with Oscillating Multi-Tool', 'Power Tools', ()),
    ('Work Station with Circular Saw', 'Miter Saws', ()),
    ('Table Saw Stand with Blade Set', 'Power Tools', ()),
    ('Dust Extractor Bag with Filter', 'Power Tools', ()),
    ('Table Saw Fence with Blade', 'Power Tools', ()),
    ('Router Base with Drill Bits', 'Power Tools', ()),
    ('Track Saw Guide with Blade Set', 'Power Tools', ()),
    ('Circular Saw Case with Replacement Blade', 'Power Tools', ()),
    ('Table Saw Guard with Blade', 'Power Tools', ()),
    ('Bundle with Circular Saw', 'Bundles', ()),
    ('Cordless Drill with Bits', 'Drill Bits', ()),
    ('Dust Collector with Filter', 'Dust Collector Parts', ()),
    ('Orbital Sander Bundle with Filter Bags', 'Consumables', ()),
    ('Blade Right Circular Saw Replacement Blade', 'Power Tools', ()),
    ('Circular Saw with Reconditioned Blade', 'Power Tools', ()),
    ('Circular Saw with Blade', 'Power Tools', ('open_box',)),
    ('Fein E-Cut Long Life Saw Blade Starlock, 1-3/8 in, 50-Pack 63502160250', 'Consumables', ()),
    ('Powermatic PM1250 Micro Dust Air Filtration System 1791331', 'Air Filtration', ()),
    ('Fixed-Base Router Stand with Blade Set', 'Power Tools', ()),
    ('Replacement Dust Collector Filter with Saw', 'Filters', ()),
    ('Circular Saw with Blade', 'Consumable', ()),
    ('Bundle with Circular Saw Blade', 'Table Saw', ()),
    ('Tool Set with Blade', 'Table Saw', ()),
])
def test_included_wording_does_not_admit_accessory_primary_or_bad_condition(name, kind, tags):
    product = Product(name, 'https://example.com/products/tool', 300, 500,
                      product_type=kind, tags=tags)
    assert classify(product) is None


def test_fixed_bundle_normalization_preserves_exact_offer_and_format():
    from datetime import UTC, datetime

    from deal_common.catalog.query import query
    from deal_common.catalog.refresh import normalize
    from deal_common.offers import VariantOffer
    from tool_deals.catalog import CATALOG

    url = ('https://beavertools.com/products/'
           'festool-rts-400-orbital-sander-ct-26-ei-hepa-dust-extractor-bundle-w-abrasives-filter-bags-rts-ct26')
    product = Product(
        'Festool RTS 400 Orbital Sander + CT 26 EI HEPA Dust Extractor Bundle w/ Abrasives & Filter Bags RTS+CT26',
        url, 1248, 1385, brand='Festool', product_type='Power Tools',
        offers=[VariantOffer(
            variant_key='67863854284893', url=url + '?variant=67863854284893',
            current_price=1248, original_price=1385, availability='in_stock',
        )],
    )
    normalized = normalize([product], CATALOG, 'beavertools.com')
    assert len(normalized) == 1
    assert normalized[0]['format'] == 'Bundle'
    assert normalized[0]['platform'] == ''
    assert 'Bundle' in CATALOG.formats
    source = {'name': 'Beaver Industrial Supply', 'successful_at': datetime.now(UTC).isoformat(),
              'products': normalized}
    filters = {'min_reference': 200, 'max_price': 0, 'min_discount': 0,
               'stock': True, 'page': 1, 'format': 'Bundle'}
    result = query([source], filters)
    assert result['total'] == 1
    card = result['cards'][0]
    assert card['category'] == 'Workshop equipment'
    assert card['offer']['variant_key'] == '67863854284893'
    assert card['offer']['url'] == url + '?variant=67863854284893'
    assert (card['offer']['current_price'], card['offer']['original_price']) == (1248, 1385)
    assert card['offer']['availability'] == 'in_stock'
    assert query([source], {**filters, 'format': 'Kit'})['total'] == 0
