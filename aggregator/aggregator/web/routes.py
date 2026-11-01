"""API and page routes for the aggregator web UI."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
from typing import Annotated
from pydantic import BeforeValidator

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates

from datetime import datetime, timedelta

from aggregator.auth import is_public_mode, require_invite
from aggregator.config import CATEGORY_RULES, STORES
from aggregator.db import (
    count_with_length, get_brands, get_category_counts, query_deals, store_status, refresh_status,
)
from aggregator.web.invite_routes import _landing_context

from aggregator.web.seo import CATEGORIES, page_context, site_url

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR), context_processors=[page_context])
templates.env.auto_reload = True

router = APIRouter()

TAX_FREE_STORES = {s.name for s in STORES if s.tax_free}
STORE_DOMAINS = {s.name: s.domain for s in STORES}
# Stores that price in CAD
CAD_STORES = {s.name for s in STORES if s.currency == "CAD"}


async def _build_store_statuses() -> list[dict]:
    """Build annotated store status list with freshness indicators."""
    statuses = await store_status()
    now = datetime.now()
    for st in statuses:
        last = datetime.fromisoformat(st["last_scraped"])
        age = now - last
        st["age_hours"] = age.total_seconds() / 3600
        if age < timedelta(hours=30):
            st["freshness"] = "fresh"
        elif age < timedelta(hours=48):
            st["freshness"] = "stale"
        else:
            st["freshness"] = "old"
        st["last_scraped_fmt"] = last.strftime("%b %d, %H:%M")
        st["domain"] = STORE_DOMAINS.get(st["store"], "")
        st["tax_free"] = st["store"] in TAX_FREE_STORES
    stores_with_data = {s["store"] for s in statuses}
    for s in STORES:
        if s.name not in stores_with_data:
            statuses.append({
                "store": s.name,
                "deal_count": 0,
                "discount_count": 0,
                "last_scraped": None,
                "age_hours": None,
                "freshness": "offline",
                "last_scraped_fmt": "never",
                "domain": s.domain,
                "tax_free": s.tax_free,
            })
    runs = {row["store"]: row for row in await refresh_status()}
    for st in statuses:
        run = runs.get(st["store"], {})
        st["scrape_status"] = run.get("status", "unknown")
        st["errors"] = run.get("errors", 0)
        st["checked_at"] = run.get("checked_at")
    statuses.sort(key=lambda s: s["store"])
    return statuses


PAGE_SIZE = 60


def pagination_context(request: Request, offset: int) -> dict:
    allowed = {'category', 'store', 'brand', 'min_discount', 'min_price', 'max_price',
               'sort', 'tax_free', 'q', 'size_min', 'size_max', 'reviewed', 'currency'}
    params = {key: value for key, value in request.query_params.items() if key in allowed}
    params['offset'] = offset + PAGE_SIZE
    query = urlencode({key: value for key, value in params.items() if value != ''})
    previous = None
    if offset:
        params['offset'] = max(0, offset - PAGE_SIZE)
        previous = '/?' + urlencode(params) + '#catalog-heading'
    return {'next_page_url': '/?' + query + '#catalog-heading',
            'next_fragment_url': '/deals?' + query, 'previous_page_url': previous}

Price = Annotated[float, Query(ge=0), BeforeValidator(lambda value: 0 if value == "" else value)]
Length = Annotated[int | None, Query(ge=100, le=220), BeforeValidator(lambda value: None if value == "" else value)]


async def _fetch_deals(
    *,
    category: str | None,
    store: str | None,
    brand: str | None,
    min_discount: float,
    min_price: float = 0,
    max_price: float = 0,
    sort: str,
    tax_free: str,
    q: str,
    size_min: int | None,
    size_max: int | None,
    reviewed: str,
    offset: int = 0,
    count: bool = True,
    currency: str = "",
) -> tuple[list, bool, int | None]:
    """Fetch a page of deals. Reviews are pre-joined via deal_reviews table."""
    if max_price > 0 and min_price > max_price:
        raise HTTPException(422, 'The maximum price must be at least the minimum price.')
    if size_min is not None and size_max is not None and size_min > size_max:
        raise HTTPException(422, 'The maximum length must be at least the minimum length.')
    tax_free_only = tax_free == "1"
    reviewed_only = reviewed == "1"

    deals = await query_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        min_price=min_price, max_price=max_price,
        sort_by=sort, limit=PAGE_SIZE + 1, offset=offset,
        tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
        q=q, size_min=size_min, size_max=size_max,
        reviewed_only=reviewed_only, currency=currency,
    )
    has_more = len(deals) > PAGE_SIZE
    deals = deals[:PAGE_SIZE]

    deal_count = None
    if count:
        deal_count = await query_deals(
            category=category, store=store, brand=brand, min_discount=min_discount,
            min_price=min_price, max_price=max_price, sort_by=sort,
            tax_free_only=tax_free_only, tax_free_stores=TAX_FREE_STORES,
            q=q, size_min=size_min, size_max=size_max,
            reviewed_only=reviewed_only, currency=currency, count_only=True,
        )

    return deals, has_more, deal_count


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = Query(0, alias="min_discount"),
    min_price: Price = 0,
    max_price: Price = 0,
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
    size_min: Length = None,
    size_max: Length = None,
    reviewed: str = Query("", alias="reviewed"),
    currency: str = Query("", pattern="^(USD|CAD)?$"),
    offset: int = Query(0, ge=0, le=100000),
):
    if not currency and (min_price > 0 or max_price > 0 or sort in {'price_low', 'price_high'}):
        currency = 'USD'
    if not is_public_mode() and not await require_invite(request):
        ctx = await _landing_context()
        return templates.TemplateResponse(
            request=request, name="invite.html", context=ctx,
        )

    deals, has_more, deal_count = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        min_price=min_price, max_price=max_price,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed, currency=currency, offset=offset,
    )
    brands = await get_brands()
    length_count = await count_with_length()
    category_counts = await get_category_counts()
    store_statuses = await store_status()
    store_counts = {s["store"]: s["deal_count"] for s in store_statuses}

    return templates.TemplateResponse(
        request=request, name="index.html",
        context={
            "deals": deals,
            "deal_count": deal_count,
            "categories": list(dict.fromkeys(cat for cat, _ in CATEGORY_RULES if cat != "boots")),
            "stores": [s.name for s in STORES],
            "brands": brands,
            "tax_free_stores": TAX_FREE_STORES,
            "cad_stores": CAD_STORES,
            "category_counts": category_counts,
            "store_counts": store_counts,
            "current_currency": currency,
            "current_category": category,
            "current_store": store,
            "current_brand": brand,
            "current_min_discount": min_discount,
            "current_min_price": min_price,
            "current_max_price": max_price,
            "current_sort": sort,
            "current_tax_free": tax_free,
            "current_reviewed": reviewed,
            "current_q": q,
            "current_size_min": size_min,
            "current_size_max": size_max,
            "length_count": length_count,
            "has_more": has_more,
            **pagination_context(request, offset),
        },
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Serve search-engine crawl rules."""
    if is_public_mode():
        return PlainTextResponse(
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /invite\n"
            "Disallow: /api/\n"
            "Disallow: /deals\n"
            "Disallow: /alerts/remove\n"
            f"Sitemap: {site_url()}/sitemap.xml\n"
        )
    # In private mode, allow the landing/invite page to be indexed but block content
    return PlainTextResponse(
        "User-agent: *\n"
        "Allow: /$\n"
        "Allow: /invite\n"
        "Disallow: /deals\n"
        "Disallow: /status\n"
        "Disallow: /admin\n"
        "Disallow: /api/\n"
    )


@router.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Dedicated store status dashboard."""
    statuses = await _build_store_statuses()
    total_deals = sum(s["deal_count"] for s in statuses)
    total_discounts = sum(s["discount_count"] for s in statuses)
    online = sum(1 for s in statuses if s["freshness"] == "fresh" and s["scrape_status"] == "ok")
    return templates.TemplateResponse(
        request=request, name="status.html",
        context={
            "page_title": "Store Report — Retailer Coverage | FreshPowder",
            "page_description": "See which stores were checked, partial results and the freshness of FreshPowder listings.",
            "store_statuses": statuses,
            "total_deals": total_deals,
            "total_discounts": total_discounts,
            "online_count": online,
            "total_count": len(statuses),
        },
    )


@router.get("/deals", response_class=HTMLResponse)
async def deals_fragment(
    request: Request,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = Query(0, alias="min_discount"),
    min_price: Price = 0,
    max_price: Price = 0,
    sort: str = Query("discount_pct", alias="sort"),
    tax_free: str = Query("", alias="tax_free"),
    q: str = Query("", alias="q"),
    size_min: Length = None,
    size_max: Length = None,
    reviewed: str = Query("", alias="reviewed"),
    currency: str = Query("", pattern="^(USD|CAD)?$"),
    offset: int = Query(0, alias="offset", ge=0),
):
    """htmx partial — returns deal cards for dynamic filtering."""
    is_load_more = offset > 0
    deals, has_more, deal_count = await _fetch_deals(
        category=category, store=store, brand=brand, min_discount=min_discount,
        min_price=min_price, max_price=max_price,
        sort=sort, tax_free=tax_free, q=q, size_min=size_min, size_max=size_max,
        reviewed=reviewed, currency=currency, offset=offset, count=not is_load_more,
    )

    template = "partials/more_cards.html" if is_load_more else "partials/deal_cards.html"
    return templates.TemplateResponse(
        request=request, name=template,
        context={"deals": deals, "deal_count": deal_count,
                 "tax_free_stores": TAX_FREE_STORES, "cad_stores": CAD_STORES,
                 "has_more": has_more, **pagination_context(request, offset),
                 "current_currency": currency, "current_q": q, "current_min_discount": min_discount,
                 "current_max_price": max_price, "current_category": category},
    )


@router.get("/healthz")
async def healthz():
    """Public, non-sensitive snapshot identity for deployment verification."""
    from fastapi.responses import JSONResponse
    try:
        rows = await refresh_status()
        checked_at = max((row["checked_at"] for row in rows), default=None)
        age = (datetime.utcnow() - datetime.fromisoformat(checked_at)).total_seconds() / 3600 if checked_at else None
        return JSONResponse({"status": "ok" if age is not None and age < 48 else "stale",
                             "checked_at": checked_at, "stores_with_deals": sum(row["deals"] > 0 for row in rows)},
                            headers={"Cache-Control": "no-store"})
    except Exception:
        return JSONResponse({"status": "unavailable", "checked_at": None}, status_code=503,
                            headers={"Cache-Control": "no-store"})


@router.get('/gear/{slug}', response_class=HTMLResponse)
async def category_page(request: Request, slug: str, page: int = Query(1, ge=1, le=1000)):
    if slug not in CATEGORIES:
        raise HTTPException(404)
    title, category, intro = CATEGORIES[slug]
    deals = await query_deals(category=category, limit=61, offset=(page - 1) * 60)
    count = await query_deals(category=category, count_only=True)
    if page > 1 and not deals:
        raise HTTPException(404)
    canonical = site_url() + '/gear/' + slug + (f'?page={page}' if page > 1 else '')
    return templates.TemplateResponse(request=request, name='category.html', context={
        'category_title': title, 'category_intro': intro, 'category': category,
        'slug': slug, 'page': page, 'deals': deals[:60], 'has_more': len(deals) > 60,
        'deal_count': count, 'cad_stores': CAD_STORES, 'tax_free_stores': TAX_FREE_STORES,
        'page_title': title + ' — Compare Prices & Sizes | FreshPowder',
        'page_description': intro, 'canonical_url': canonical,
        'noindex': any(key != 'page' for key in request.query_params),
        'structured_data': {'@context': 'https://schema.org', '@type': 'CollectionPage',
                            'name': title, 'description': intro, 'url': canonical},
    })


@router.get('/sitemap.xml')
async def sitemap():
    from xml.sax.saxutils import escape
    if not is_public_mode():
        raise HTTPException(404)
    paths = ['/', '/alerts', '/status', '/privacy'] + ['/gear/' + slug for slug in CATEGORIES]
    body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    body += ''.join('<url><loc>' + escape(site_url() + path) + '</loc></url>' for path in paths)
    return Response(body + '</urlset>', media_type='application/xml')


@router.get('/privacy', response_class=HTMLResponse)
async def privacy_page(request: Request):
    return templates.TemplateResponse(request=request, name='privacy.html', context={
        'page_title': 'Email Signup & Privacy | FreshPowder',
        'page_description': 'How FreshPowder handles optional email signups, withdrawal and browsing information.',
    })
