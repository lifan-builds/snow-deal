"""Web route integration tests for auth, SEO, and rate limiting."""

from __future__ import annotations

import asyncio
from datetime import datetime
from functools import partial

import pytest
from fastapi.testclient import TestClient

import aggregator.auth_db as auth_db_module
import aggregator.db as db_module
import aggregator.web.app as app_module
import aggregator.web.routes as routes_module
from aggregator.models import AggregatedDeal
from aggregator.web import admin_routes, event_routes, invite_routes


def _make_deal(name: str = "Atomic Bent 100", store: str = "Evo") -> AggregatedDeal:
    return AggregatedDeal(
        id=None,
        store=store,
        name=name,
        url=f"https://example.com/{name.replace(' ', '-').lower()}",
        current_price=499.99,
        original_price=599.99,
        discount_pct=16.5,
        category="skis",
        sizes=None,
        length_min=None,
        length_max=None,
        scraped_at=datetime.now(),
    )


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    deals_db = tmp_path / "deals.db"
    auth_db_path = tmp_path / "auth.db"

    monkeypatch.setenv("AUTH_DB_PATH", str(auth_db_path))
    monkeypatch.delenv("TURSO_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

    async def _init_test_db():
        await db_module.init_db(deals_db)

    monkeypatch.setattr(app_module, "init_db", _init_test_db)
    monkeypatch.setattr(routes_module, "query_deals", partial(db_module.query_deals, db_path=deals_db))
    monkeypatch.setattr(routes_module, "get_brands", partial(db_module.get_brands, db_path=deals_db))
    monkeypatch.setattr(routes_module, "get_category_counts", partial(db_module.get_category_counts, db_path=deals_db))
    monkeypatch.setattr(routes_module, "count_with_length", partial(db_module.count_with_length, db_path=deals_db))
    monkeypatch.setattr(routes_module, "store_status", partial(db_module.store_status, db_path=deals_db))

    auth_db_module._conn = None
    auth_db_module.TURSO_URL = ""
    auth_db_module.TURSO_AUTH_TOKEN = ""
    invite_routes.invite_submit_limiter.clear()
    admin_routes.admin_create_codes_limiter.clear()
    event_routes.event_post_limiter.clear()

    yield deals_db

    auth_db_module._conn = None


def test_private_mode_serves_public_landing_without_session(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    with TestClient(app_module.create_app()) as client:
        home = client.get("/", follow_redirects=False)
        protected = client.get("/deals", follow_redirects=False)

    assert home.status_code == 200
    assert "FreshPowder" in home.text
    assert "affiliate_app_confirm.php" not in home.text
    assert protected.status_code == 302
    assert protected.headers["location"] == "/invite"


def test_private_mode_requires_secret_key(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
        with TestClient(app_module.create_app()):
            pass


def test_public_mode_serves_homepage_and_public_robots(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    asyncio.run(db_module.init_db(isolated_app))
    asyncio.run(db_module.upsert_deals([_make_deal()], isolated_app))

    with TestClient(app_module.create_app()) as client:
        home = client.get("/")
        robots = client.get("/robots.txt")
        admin = client.get("/admin/codes", follow_redirects=False)

    assert home.status_code == 200
    assert "FreshPowder" in home.text
    assert 'property="og:title"' in home.text
    assert robots.status_code == 200
    assert "Allow: /" in robots.text
    assert "Disallow: /admin" in robots.text
    assert admin.status_code == 302
    assert admin.headers["location"] == "/"


def test_vercel_runtime_validates_deals_db_without_migrations(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "1")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    asyncio.run(db_module.init_db(isolated_app))

    called = {"ensure": False}

    async def _unexpected_init_db():
        raise AssertionError("init_db should not run in read-only Vercel runtime")

    async def _ensure_deals_db_ready():
        called["ensure"] = True

    monkeypatch.setattr(app_module, "init_db", _unexpected_init_db)
    monkeypatch.setattr(app_module, "ensure_deals_db_ready", _ensure_deals_db_ready)

    with TestClient(app_module.create_app()) as client:
        response = client.get("/robots.txt")

    assert response.status_code == 200
    assert called["ensure"] is True


def test_invite_submission_sets_session_cookie(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    async def _valid_code(code: str) -> bool:
        return code == "FRESH123"

    async def _record_code_use(code: str) -> None:
        return None

    monkeypatch.setattr(invite_routes, "validate_invite_code", _valid_code)
    monkeypatch.setattr(invite_routes, "record_code_use", _record_code_use)

    with TestClient(app_module.create_app()) as client:
        response = client.post("/invite", data={"code": "fresh123"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "snow_deals_session=" in response.headers["set-cookie"]


def test_mutating_routes_are_rate_limited(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setattr(invite_routes, "INVITE_SUBMIT_LIMIT", 1)
    monkeypatch.setattr(event_routes, "EVENT_POST_LIMIT", 1)
    invite_routes.invite_submit_limiter.clear()
    event_routes.event_post_limiter.clear()

    with TestClient(app_module.create_app()) as client:
        first_invite = client.post("/invite", data={"code": "badcode"})
        second_invite = client.post("/invite", data={"code": "badcode"})
        first_event = client.post("/api/event", json={"event_type": "page_view"})
        second_event = client.post("/api/event", json={"event_type": "page_view"})

    assert first_invite.status_code == 200
    assert second_invite.status_code == 429
    assert "Too many invite attempts" in second_invite.text
    assert first_event.status_code == 200
    assert second_event.status_code == 429
    assert second_event.json()["error"] == "rate_limited"


def test_blank_numeric_filters_and_currency(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "1")
    asyncio.run(db_module.init_db(isolated_app))
    asyncio.run(db_module.upsert_deals([_make_deal()], isolated_app))
    with TestClient(app_module.create_app()) as client:
        response = client.get('/?min_price=&max_price=&size_min=&size_max=&currency=USD')
        assert response.status_code == 200
        assert 'Atomic Bent 100' in response.text
        assert client.get('/deals?currency=EUR').status_code == 422
        assert client.get('/deals?offset=-1').status_code == 422


def test_public_health_and_store_report_use_isolated_snapshot(isolated_app, monkeypatch):
    monkeypatch.setenv("PUBLIC_MODE", "0")
    monkeypatch.setenv("SECRET_KEY", "test-health-secret-at-least-32-characters")
    monkeypatch.setattr(routes_module, "refresh_status", partial(db_module.refresh_status, db_path=isolated_app))
    with TestClient(app_module.create_app()) as client:
        response = client.get('/healthz')
        assert response.status_code == 200
        assert response.json()['status'] == 'stale'
        assert response.headers['cache-control'] == 'no-store'
        assert client.get('/status').status_code == 200
        assert client.get('/deals', follow_redirects=False).status_code == 302


def test_waitlist_failure_is_not_reported_as_success(isolated_app, monkeypatch):
    async def broken_waitlist(email):
        raise RuntimeError('simulated outage')
    monkeypatch.setenv("PUBLIC_MODE", "1")
    monkeypatch.setattr(invite_routes, "add_to_waitlist", broken_waitlist)
    with TestClient(app_module.create_app()) as client:
        assert client.post('/waitlist', data={'email':'invalid'}).status_code == 422
        response = client.post('/waitlist', data={'email':'test@example.com'})
        assert response.status_code == 503
        assert response.json()['ok'] is False


def test_public_category_seo_and_pagination(isolated_app, monkeypatch):
    monkeypatch.setenv('PUBLIC_MODE', '1')
    monkeypatch.setenv('SITE_URL', 'https://freshpowder.clifan.com')
    with TestClient(app_module.create_app()) as client:
        asyncio.run(db_module.upsert_deals([_make_deal()], db_path=isolated_app))
        home = client.get('/')
        category = client.get('/gear/skis')
        filtered = client.get('/?q=Atomic')
        assert home.status_code == category.status_code == 200
        assert 'No invite or account needed' in home.text
        assert 'Ski deals — Compare Prices &amp; Sizes' in category.text
        assert 'https://freshpowder.clifan.com/gear/skis' in category.text
        assert 'application/ld+json' in category.text
        assert 'Atomic Bent 100' in category.text
        assert 'noindex,follow' not in category.text
        assert 'noindex,follow' in filtered.text
        assert client.get('/gear/not-a-category').status_code == 404
        assert client.get('/gear/skis?page=1000').status_code == 404
        assert client.get('/admin/codes', follow_redirects=False).status_code == 302
        assert 'https://freshpowder.clifan.com/sitemap.xml' in client.get('/robots.txt').text
        assert '/gear/snowboards' in client.get('/sitemap.xml').text


def test_prelaunch_signup_persistence_dedup_and_removal(isolated_app, monkeypatch):
    from aggregator.web.signup_routes import signup_limiter
    signup_limiter.clear()
    monkeypatch.setenv('PUBLIC_MODE', '1')
    with TestClient(app_module.create_app()) as client:
        response = client.post('/alerts/signup', data={'email':'  TEST@example.com  '}, headers={'accept':'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'coming soon' in data['message']
        assert response.headers['cache-control'] == 'no-store'
        token = data['removal_token']
        duplicate = client.post('/alerts/signup', data={'email':'test@example.com'}, headers={'accept':'application/json'})
        assert duplicate.json()['removal_token'] is None
        import sqlite3, os
        conn = sqlite3.connect(os.environ['AUTH_DB_PATH'])
        row = conn.execute('SELECT email, consent_version, removal_hash FROM deal_alert_signups').fetchone()
        assert row[0] == 'test@example.com'
        assert row[1] == 'rare-deals-prelaunch-v1'
        assert row[2] != token
        assert conn.execute('SELECT count(*) FROM waitlist').fetchone()[0] == 0
        assert client.post('/alerts/remove', data={'token':token}).status_code == 200
        assert conn.execute('SELECT count(*) FROM deal_alert_signups').fetchone()[0] == 0
        conn.close()


def test_signup_validation_storage_failure_and_no_js(isolated_app, monkeypatch):
    from aggregator.web import signup_routes
    signup_routes.signup_limiter.clear()
    monkeypatch.setenv('PUBLIC_MODE', '1')
    with TestClient(app_module.create_app()) as client:
        assert client.post('/alerts/signup', data={'email':'bad'}).status_code == 422
        assert client.post('/alerts/signup', data={'email':'test@example.com','website':'spam'}).status_code == 200
        response = client.post('/alerts/signup', data={'email':'test@example.com'})
        assert response.status_code == 200
        assert 'Your private removal link' in response.text
        def fail():
            raise RuntimeError('test database failure')
        monkeypatch.setattr(signup_routes, 'signup_db', fail)
        assert client.post('/alerts/signup', data={'email':'new@example.com'}).status_code == 503


def test_full_page_pagination_and_currency_match_results(isolated_app, monkeypatch):
    from bs4 import BeautifulSoup
    from urllib.parse import urlsplit, parse_qs
    monkeypatch.setenv('PUBLIC_MODE', '1')
    observed = []
    asyncio.run(db_module.init_db(isolated_app))

    async def fake_query(**kwargs):
        observed.append(kwargs)
        if kwargs.get('count_only'):
            return 125
        start = kwargs.get('offset', 0)
        return [_make_deal(f'Ski {i}') for i in range(start, min(start + kwargs.get('limit', 61), 125))]

    monkeypatch.setattr(routes_module, 'query_deals', fake_query)
    with TestClient(app_module.create_app(enable_lifespan=False)) as client:
        first = BeautifulSoup(client.get('/?q=ski&max_price=99.95&sort=price_low&unrelated=private-value').text, 'html.parser')
        assert first.select_one('input[name=max_price]')['value'] == '99.95'
        assert first.select_one('select[name=currency] option[selected]')['value'] == 'USD'
        link = first.select_one('.load-more-wrap a')
        assert 'private-value' not in link['href']
        assert parse_qs(urlsplit(link['href']).query)['offset'] == ['60']
        second = BeautifulSoup(client.get(link['href']).text, 'html.parser')
        assert len(second.select('.deal-card')) == 60
        assert 'Ski 60' in second.select_one('.deal-card').text
        assert 'Previous results' in second.text
        assert any(row.get('offset') == 60 and row.get('currency') == 'USD' for row in observed)
        fragment = BeautifulSoup(client.get(link['hx-get']).text, 'html.parser')
        assert 'offset=120' in fragment.select_one('.load-more-wrap a')['href']


def test_browser_errors_are_pages_and_api_errors_remain_json(isolated_app, monkeypatch):
    monkeypatch.setenv('PUBLIC_MODE', '1')
    with TestClient(app_module.create_app(enable_lifespan=False)) as client:
        missing = client.get('/not-a-page', headers={'Accept': 'text/html'})
        assert missing.status_code == 404
        assert 'Browse all deals' in missing.text
        invalid = client.get('/?min_price=invalid', headers={'Accept': 'text/html'})
        assert invalid.status_code == 422
        assert 'Check your filters' in invalid.text
        assert client.get('/?min_price=200&max_price=100').status_code == 422
        assert client.get('/?size_min=180&size_max=160').status_code == 422
        assert client.get('/api/not-a-route').headers['content-type'].startswith('application/json')


def test_signup_html_errors_and_removal_failure_are_recoverable(isolated_app, monkeypatch):
    from aggregator.web import signup_routes
    monkeypatch.setenv('PUBLIC_MODE', '1')
    with TestClient(app_module.create_app(enable_lifespan=False)) as client:
        invalid = client.post('/alerts/signup', data={'email': 'invalid'}, headers={'Accept': 'text/html'})
        assert invalid.status_code == 422
        assert 'Please enter a valid email address.' in invalid.text
        assert 'Try again' in invalid.text
        assert invalid.headers['cache-control'] == 'no-store'
        invalid_code = client.post('/alerts/remove', data={'token': 'invalid'}, headers={'Accept': 'text/html'})
        assert invalid_code.status_code == 422
        assert 'complete private code' in invalid_code.text

        def unavailable():
            raise RuntimeError('test storage failure')

        monkeypatch.setattr(signup_routes, 'signup_db', unavailable)
        failed = client.post('/alerts/remove', data={'token': 'a' * 43}, headers={'Accept': 'text/html'})
        assert failed.status_code == 503
        assert 'We could not remove your signup' in failed.text
        assert failed.headers['cache-control'] == 'no-store'
