import pytest

from tool_deals.catalog import classify
from deal_common.models import Product


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
    ('Oscillating Multi-Tool Blade Kit', "Power Tools", None, "", ""),
    ('Kreg Precision Router Table System', "", None, "", ""),
    ('SCM Formula Band Saw (Showroom Model)', "Machinery", None, "", ""),
    ('Display Model Table Saw', "Table Saws", None, "", ""),
    ('Demo CNC Router', "CNC Router", None, "", ""),
    ('CNC Router with Digital Display', "CNC Router", "Workshop equipment", "Not specified", ""),
    ("20V Brushless Handheld Planer - Tool Only", "Planers", "Power tools", "Bare tool", ""),
])
def test_scope_package_and_platform(name, kind, category, form, platform):
    actual = classify(Product(name, "https://example.com", 200, 500, product_type=kind))
    if category is None:
        assert actual is None
    else:
        assert (actual.category, actual.format, actual.platform) == (category, form, platform)


def test_brand_aliases_merge_only_explicit_manufacturer_names():
    from tool_deals.catalog import CATALOG
    from deal_common.catalog.refresh import normalize
    from deal_common.offers import VariantOffer
    for brand, expected in [("Sawstop", "SawStop"), ("Jet Tools", "JET"), ("Kreg Tool", "Kreg"),
                            ("Different Tools", "Different Tools")]:
        product = Product("Table Saw", "https://example.com/products/saw", 200, 500, brand=brand,
                          offers=[VariantOffer(variant_key="1", url="https://example.com/products/saw?variant=1",
                                               current_price=200, original_price=500, availability="in_stock")])
        assert normalize([product], CATALOG, "example.com")[0]["brand"] == expected
