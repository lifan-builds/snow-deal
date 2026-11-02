"""Original buying explanations; no product-testing or live-price claims."""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from aggregator.web.routes import templates
from aggregator.web.seo import site_url

GUIDES = {
    "check-a-real-ski-deal": {
        "title": "How to check whether a ski or snowboard deal is worth buying",
        "description": "Compare the exact model, usable size and observed price history before trusting a large discount.",
        "sections": [
            ("Start with the price you can actually pay", [
                "A large percentage off is a comparison with the retailer’s reference price. It does not tell you whether another shop sells the same gear for less, whether your size is available, or whether this is an unusual price.",
                "Start with the exact model, model year and size you would buy. Keep a ski-and-binding package separate from flat skis, and a wide snowboard separate from its regular-width version. A lower price on a different configuration is an alternative, not a cheaper offer for the same item." ]),
            ("Check three prices, not just one percentage", [
                "First, check today’s retailer listing. Second, compare current listings for the same configuration at other shops. Third, examine the prices observed over time. These answer different questions: what a shop asks now, what alternatives exist now, and how today compares with the recorded past.",
                "For example, a hypothetical $400 item marked down from $800 is 50% off that reference price. If another shop offers the same configuration for $350, the larger advertised discount did not find the cheaper purchase. This is an illustration, not a current offer." ]),
            ("Read the limits of the history", [
                "FreshPowder shows the observations it has collected, not every price that ever existed. One observed day cannot establish a 30-day low. Gaps between observations do not mean the price stayed unchanged.",
                "Our chart follows matched retailer listings. Available sizes may change, and a retailer’s starting price may belong to a different size. Treat an observed listing low as context; confirm the price for your chosen size at checkout." ]),
            ("Decide whether the offer is useful to you", [
                "Check condition, shipping, taxes, returns and warranty coverage at the retailer. A cheaper used or demo item may have different wear and return terms. If those costs or terms are unknown, do not treat the displayed listing price as the delivered total.",
                "A good buying decision is an appropriate item in your size at an acceptable final price. If the offer only fits someone else, a bigger discount does not improve it. FreshPowder compares listings; it does not replace equipment fitting or the shop’s final availability check." ]),
        ],
    },
    "new-past-season-demo-gear": {
        "title": "New, past-season, blemished or demo gear: what are you comparing?",
        "description": "Keep condition, model year and package contents separate when comparing ski and snowboard prices.",
        "sections": [
            ("Past-season describes the model year, not the condition", [
                "A previous-season model can still be unused. A current-season item can be used. Treat model year and condition as separate facts, and check both in the retailer’s listing rather than inferring condition from the size of the discount.",
                "A familiar model name can survive changes between seasons. Compare the specific year and configuration. FreshPowder’s reviewed model pages keep different model years separate instead of merging similar names into one price." ]),
            ("Blemished does not tell you the whole story", [
                "A retailer may use ‘blem’ for a cosmetic imperfection, but the listing must explain what is affected. Read the description, photographs, warranty and return terms for that particular item. Do not assume every blemished item has the same warranty as an unblemished one.",
                "A discount only becomes comparable after the condition is clear. If damage or coverage is not explained, ask the retailer before buying; missing information is not proof that the issue is cosmetic." ]),
            ("Demo and used items need item-specific checks", [
                "Demo equipment has been used. Check the actual item’s wear, repairs, mounting history and included components, rather than relying on a stock photograph. Listings may grade condition differently across shops.",
                "For skis sold with bindings, confirm what is included and have a qualified shop assess condition, boot compatibility and setup. A package price cannot be compared directly with flat skis, and this guide cannot determine whether used equipment is suitable or safe for a particular rider." ]),
            ("Make a short comparison before checkout", [
                "Record the exact model and year, length/width, new or used condition, included bindings or other components, final price, and return/warranty terms. Separate alternatives into their own rows. Do not allow a lower price to hide a different product.",
                "FreshPowder’s equipment feed can surface different kinds of listings. Read the retailer title and condition details every time. Our model pages use reviewed identity matches; they are a price-comparison aid, not an inspection of the physical item." ]),
        ],
    },
    "listed-price-and-your-size": {
        "title": "Why the cheapest listed price may not be your size",
        "description": "Understand reported sizes, starting prices, wide boards and currency before choosing a ski or snowboard offer.",
        "sections": [
            ("A product page can contain several prices", [
                "Retailers can price variants differently. The price shown on a category card or feed may be a starting price, while the length or size you select costs more. Finding your size in a listing does not prove that the lowest displayed price applies to it.",
                "Use FreshPowder to find candidate shops, then select your exact variant on the retailer page. Confirm the resulting price and stock status before making a decision. We label retailer listing prices separately from reported sizes because those fields do not always establish a variant-level offer." ]),
            ("A range is not a stock list", [
                "If a source describes a product as spanning 160–180 cm, that does not prove 170 cm is available. Exact-size comparisons need explicitly reported choices. FreshPowder’s model-page size filter excludes listings that do not explicitly report the selected size.",
                "That conservative choice can hide a shop whose size data is missing. Clear the filter to see the broader comparison and check unknown-size listings directly. Missing size information means unknown, not necessarily out of stock." ]),
            ("Keep width and currency explicit", [
                "A snowboard marked W or wide is not automatically the same variant as a regular board of the same nominal length. Keep the full designation when comparing. Likewise, a USD price and a CAD price are not directly interchangeable.",
                "FreshPowder separates currencies instead of converting them into one ranking. Shipping destination, tax, import costs and returns can change a cross-border purchase. Check the retailer’s final terms instead of assuming the smaller number is cheaper." ]),
            ("Size filtering helps shopping, not fitting", [
                "A filter can narrow listings to a size you request; it cannot decide whether that size is right for your needs. In particular, a discounted boot still needs appropriate fit, and equipment compatibility should be checked with a qualified shop.",
                "When sharing a model with someone, explain the size and currency you checked. The comparison link opens a model page whose offers may change later. Recheck availability before treating a shared price as a current deal." ]),
        ],
    },
}

guide_router = APIRouter()


@guide_router.get('/guides', response_class=HTMLResponse)
async def guide_index(request: Request):
    return templates.TemplateResponse(request=request, name='guides.html', context={
        'guides': GUIDES, 'page_title': 'Ski & Snowboard Deal Buying Guides | FreshPowder',
        'page_description': 'Practical explanations of discounts, equipment condition, reported sizes and price comparisons.',
    })


@guide_router.get('/guides/{slug}', response_class=HTMLResponse)
async def guide_page(request: Request, slug: str):
    guide = GUIDES.get(slug)
    if not guide:
        raise HTTPException(404)
    canonical = site_url() + '/guides/' + slug
    return templates.TemplateResponse(request=request, name='guide.html', context={
        'guide': guide, 'guides': GUIDES, 'slug': slug,
        'page_title': guide['title'] + ' | FreshPowder', 'page_description': guide['description'],
        'canonical_url': canonical,
        'breadcrumb_data': {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Buying guides', 'item': site_url()+'/guides'},
            {'@type': 'ListItem', 'position': 2, 'name': guide['title'], 'item': canonical},
        ]},
    })


@guide_router.get('/about', response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse(request=request, name='about.html', context={
        'page_title': 'About & Contact | FreshPowder',
        'page_description': 'Who builds FreshPowder, how to report an incorrect offer, and what our comparisons cover.',
    })
