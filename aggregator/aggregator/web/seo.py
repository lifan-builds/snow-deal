"""Small, crawlable category directory and shared page metadata."""

import os

CATEGORIES = {
    "skis": (
        "Ski deals",
        "skis",
        "Compare discounted skis across independent shops and major retailers. Check the model year, waist width and available length before choosing a pair.",
    ),
    "snowboards": (
        "Snowboard deals",
        "snowboards",
        "Find snowboard sales with retailer prices and reported sizes. Compare the exact model year, length, width and camber profile; similarly named boards can ride differently.",
    ),
    "ski-boots": (
        "Ski boot deals",
        "ski boots",
        "Browse ski boot discounts, available sizes and exact-model review links. Fit comes first: check mondo size, last width, flex and binding compatibility with a qualified boot fitter.",
    ),
    "snowboard-boots": (
        "Snowboard boot deals",
        "snowboard boots",
        "Compare snowboard boot sales across shops. Confirm your size, lacing system and binding compatibility; a large discount cannot fix a poor fit.",
    ),
    "bindings": (
        "Ski and snowboard binding deals",
        "bindings",
        "Explore binding discounts and check the exact system before buying. Ski boot sole standards, release settings and snowboard mounting systems matter more than the sale percentage.",
    ),
    "helmets": (
        "Ski and snowboard helmet deals",
        "helmets",
        "Find snow helmet discounts across retailers. Confirm the correct size, safety certification and goggle fit directly with the shop.",
    ),
}


def site_url():
    return os.environ.get("SITE_URL", "https://snow-deal.vercel.app").rstrip("/")


def page_context(request):
    path = request.url.path
    private = path.startswith(("/admin", "/invite", "/alerts/remove", "/deals"))
    return {
        "site_url": site_url(),
        "seo_defaults": {
            "canonical_url": site_url() + path,
            "page_title": "Ski & Snowboard Deals | FreshPowder",
            "page_description": "Compare ski and snowboard deals, available sizes, retailer prices and exact-model review links. Browse free. Join the list for rare-deal alerts, coming soon.",
            "noindex": private or bool(request.url.query),
        },
        "seo_categories": CATEGORIES,
    }
