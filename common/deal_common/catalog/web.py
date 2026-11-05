"""Server-rendered catalog app with read-only snapshots and validated filters."""
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from deal_common.catalog.definition import Catalog
from deal_common.catalog.health import snapshot_health
from deal_common.catalog.identity import manufacturer_name
from deal_common.catalog.query import FRESHNESS_HOURS, is_fresh, query
from deal_common.catalog.storage import read_offer_history, read_sources
from deal_common.offers import size_key

ASSETS = Path(__file__).parent


def create_app(catalog: Catalog, database: Path, *, public_url: str | None = None) -> FastAPI:
    app = FastAPI(title=catalog.name, docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=ASSETS / "static"), name="static")
    app.mount("/brand", StaticFiles(directory=catalog.assets), name="brand")
    templates = Jinja2Templates(directory=ASSETS / "templates")
    templates.env.globals["public_url"] = public_url.rstrip("/") if public_url else None
    templates.env.filters["money"] = lambda value: f"${value:,.2f}" if value % 1 else f"${value:,.0f}"
    templates.env.filters["date"] = lambda value: datetime.fromisoformat(value).strftime("%b %d, %H:%M UTC") if value else "Not yet refreshed"

    def sources():
        configured = {source.name for source in catalog.sources}
        return [row for row in read_sources(database, catalog.slug) if row["name"] in configured]

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https:; style-src 'self'; "
            "script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        # Local previews and filter permutations should not enter search indexes.
        if not public_url or request.url.query or request.url.path == "/healthz":
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, q: str = Query("", max_length=150),
              category: str = Query("", max_length=80), brand: str = Query("", max_length=100),
              store: str = Query("", max_length=100), size: str = Query("", max_length=80),
              format: str = Query("", max_length=80), platform: str = Query("", max_length=80),
              min_reference: float = Query(catalog.default_reference, ge=0, le=1000000),
              max_price: float = Query(0, ge=0, le=1000000),
              min_discount: float = Query(0, ge=0, le=100), stock: bool = False,
              page: int = Query(1, ge=1, le=100000)):
        if brand and catalog.brand_aliases:
            brand = manufacturer_name(brand, brand_aliases=catalog.brand_aliases)
        filters = {"q": q, "category": category, "brand": brand, "store": store, "size": size, "format": format,
                       "platform": platform, "min_reference": min_reference, "max_price": max_price,
                       "min_discount": min_discount, "stock": stock, "page": page}
        rows = sources()
        result = query(rows, filters, brand_aliases=catalog.brand_aliases)
        if size:
            requested_size_key = size_key(size)
            filters["size"] = next((label for label in result["facets"]["size"]
                                    if size_key(label) == requested_size_key), size)
        for card in result["cards"]:
            card["history_url"] = "/history?" + urlencode({"source": card["store"], "product": card["url"],
                                                        "variant": card["offer"]["variant_key"]})
        def page_url(number):
            return "/?" + urlencode({**filters, "page": number, "stock": str(stock).lower()}) + "#deals"
        labels = {"q": "Search", "category": "Category", "brand": "Brand", "store": "Retailer",
                  "size": catalog.size_label, "format": "Package", "platform": "Platform",
                  "min_reference": "Reference ≥ $", "max_price": "Budget ≤ $",
                  "min_discount": "Discount ≥", "stock": "Reported in stock"}
        active_filters = []
        for key, label in labels.items():
            value = filters[key]
            if not value:
                continue
            cleared = {**filters, key: 0 if key in {"min_reference", "max_price", "min_discount"} else "",
                       "stock": str(stock).lower(), "page": 1}
            if key == "stock":
                cleared[key] = "false"
            if key == "stock":
                display = label
            elif isinstance(value, (int, float)):
                display = f"{label} {value:g}"
            else:
                display = f"{label}: {value}"
            if key == "min_discount":
                display += "%"
            active_filters.append({"label": display, "url": "/?" + urlencode(cleared) + "#deals"})
        return templates.TemplateResponse(request=request, name="index.html", context={
            "catalog": catalog, "filters": filters, "result": result, "active_filters": active_filters,
            "previous": page_url(result["page"] - 1), "next": page_url(result["page"] + 1),
            "source_count": len(catalog.sources), "freshness_hours": FRESHNESS_HOURS,
        })

    @app.get("/history", response_class=HTMLResponse)
    def history(request: Request, source: str = Query(..., max_length=100),
                product: str = Query(..., max_length=2000), variant: str = Query(..., max_length=100)):
        for row in sources():
            if row["name"] != source:
                continue
            for item in row["products"]:
                if item["url"] != product:
                    continue
                for offer in item["offers"]:
                    if offer["variant_key"] == variant:
                        observations = read_offer_history(database, catalog.slug, source, item, offer,
                                                          now=datetime.now(UTC), brand_aliases=catalog.brand_aliases)
                        display_item = {**item, "brand": manufacturer_name(
                            item["brand"], brand_aliases=catalog.brand_aliases)} if catalog.brand_aliases else item
                        return templates.TemplateResponse(request=request, name="history.html", context={
                            "catalog": catalog, "product": display_item, "offer": offer, "store": source,
                            "observations": observations})
        raise HTTPException(status_code=404, detail="This variant is not in the current snapshot")

    @app.get("/sources", response_class=HTMLResponse)
    def source_health(request: Request):
        rows = {row["name"]: row for row in sources()}
        now = datetime.now(UTC)
        health = []
        for source in catalog.sources:
            row = rows.get(source.name, {})
            health.append({"name": source.name, "url": source.scrape_urls[0],
                           "checked_at": row.get("checked_at"), "successful_at": row.get("successful_at"),
                           "status": row.get("status", "Not refreshed"),
                           "fresh": is_fresh(row.get("successful_at"), now),
                           "count": len(row.get("products", [])),
                           "collections": row.get("detail", {}).get("collections", [])})
        return templates.TemplateResponse(request=request, name="sources.html", context={
            "catalog": catalog, "sources": health, "freshness_hours": FRESHNESS_HOURS})

    @app.get("/healthz")
    def health():
        return snapshot_health(catalog, sources())

    @app.get("/robots.txt", response_class=PlainTextResponse)
    def robots():
        if public_url:
            return f"User-agent: *\nAllow: /\nDisallow: /healthz\nSitemap: {public_url.rstrip('/')}/sitemap.xml\n"
        return "User-agent: *\nDisallow: /\n"

    @app.get("/sitemap.xml")
    def sitemap():
        from xml.sax.saxutils import escape
        base = escape(public_url.rstrip("/")) if public_url else ""
        entries = "".join(f"<url><loc>{base}{path}</loc></url>" for path in ("/", "/sources")) if base else ""
        return Response('<?xml version="1.0" encoding="UTF-8"?>'
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                        + entries + '</urlset>', media_type="application/xml")

    return app
