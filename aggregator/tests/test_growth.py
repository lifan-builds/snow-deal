"""Public acquisition and analytics privacy regressions; no existing data."""
import asyncio
import json
import sqlite3
from bs4 import BeautifulSoup
import pytest
from fastapi.testclient import TestClient
from aggregator import auth_db
from aggregator.web import event_routes
from aggregator.web.app import create_app
from aggregator.web.guides import GUIDES


@pytest.fixture
def public_client(monkeypatch):
    monkeypatch.setenv('PUBLIC_MODE', '1')
    monkeypatch.setenv('SITE_URL', 'https://freshpowder.clifan.com')
    event_routes.event_post_limiter.clear()
    with TestClient(create_app(enable_lifespan=False), base_url='https://freshpowder.clifan.com') as client:
        yield client


def test_anonymous_sessions_never_store_auth_tokens(public_client, monkeypatch):
    recorded = []
    async def log(**data): recorded.append(data)
    monkeypatch.setattr(event_routes, 'log_event', log)
    public_client.cookies.set('snow_deals_session', 'dummy-login-cookie')
    first = public_client.post('/api/event', json={'event_type': 'page_view', 'metadata': json.dumps({
        'page': '/products/atomic-bent-90-2026', 'source': 'x', 'campaign': '2026_winter',
        'email': 'private@example.invalid', 'q': 'private query', 'referrer': 'https://x.com/?token=private',
    })})
    second = public_client.post('/api/event', json={'event_type': 'click', 'deal_url': 'https://example.com/skis?email=private#token'})
    assert first.status_code == second.status_code == 200
    assert recorded[0]['session'] == recorded[1]['session']
    assert recorded[0]['session'].startswith('anon:')
    assert 'dummy-login-cookie' not in json.dumps(recorded)
    assert 'private' not in json.dumps(recorded)
    assert recorded[1]['deal_url'] == 'https://example.com/skis'
    assert 'HttpOnly' in first.headers['set-cookie'] and 'Max-Age=1800' in first.headers['set-cookie']
    assert 'Secure' in first.headers['set-cookie']


@pytest.mark.parametrize('headers', [{'dnt': '1'}, {'sec-gpc': '1'}])
def test_opt_out_does_not_record_or_set_cookie(public_client, monkeypatch, headers):
    async def fail(**data): raise AssertionError('must not record')
    monkeypatch.setattr(event_routes, 'log_event', fail)
    r = public_client.post('/api/event', headers=headers, json={'event_type': 'page_view'})
    assert r.json()['recorded'] is False and 'set-cookie' not in r.headers


def test_reject_cross_site_unsafe_urls_and_oversized_payload(public_client, monkeypatch):
    async def fail(**data): raise AssertionError('must not record')
    monkeypatch.setattr(event_routes, 'log_event', fail)
    assert public_client.post('/api/event', headers={'origin':'https://other.example'}, json={'event_type':'click'}).status_code == 403
    for url in ['javascript:alert(1)', 'https://user:password@example.com/item']:
        assert public_client.post('/api/event', json={'event_type':'click','deal_url':url}).status_code == 400
    assert public_client.post('/api/event', json={'event_type':'click','metadata':'a'*1001}).status_code == 422
    public_client.cookies.set('admin_key','dummy-admin-cookie')
    assert public_client.post('/api/event', json={'event_type':'page_view'}).json()['recorded'] is False


def test_metadata_rejects_private_paths_and_malformed_values():
    for raw in ['not-json', '[]', '{"source": [], "currency": {}, "campaign": []}', '{"page":"/alerts/remove/secret"}']:
        assert json.loads(event_routes.safe_metadata(raw)) == {'version': 2}


def test_stats_distinguish_legacy_events_sessions_and_clicks(monkeypatch):
    conn = sqlite3.connect(':memory:')
    for schema in auth_db.AUTH_SCHEMA: conn.execute(schema)
    monkeypatch.setattr(auth_db, '_conn', conn)
    monkeypatch.setattr(auth_db, '_sync', lambda: None)
    async def run():
        await auth_db.log_event('page_view',session='anon:a',metadata='{"source":"x"}')
        await auth_db.log_event('click',session='anon:a')
        await auth_db.log_event('click',session='anon:a')
        await auth_db.log_event('page_view',session='anon:b',metadata='{"source":"google"}')
        await auth_db.log_event('click',session='legacy-placeholder')
        return await auth_db.get_click_stats()
    stats = asyncio.run(run())
    assert stats['unique_sessions'] == 2 and stats['outbound_sessions'] == 1
    assert stats['acquisition'] == [{'source':'google','sessions':1},{'source':'x','sessions':1}]
    assert next(r['cnt'] for r in stats['by_type'] if r['event_type']=='click') == 3
    conn.close()


def test_guides_are_crawlable_linked_and_canonical(public_client):
    sitemap = public_client.get('/sitemap.xml').text
    hub = public_client.get('/guides')
    assert hub.status_code == 200
    for slug in GUIDES:
        path = '/guides/'+slug
        assert path in sitemap and path in hub.text
        page = BeautifulSoup(public_client.get(path).text, 'html.parser')
        assert len(page.select('h1')) == 1 and len(page.select('h2')) >= 4
        assert page.select_one('link[rel=canonical]')['href'] == 'https://freshpowder.clifan.com'+path
        assert not page.select_one('meta[name=robots]')
        assert page.select_one('a[href="/products"]')
        assert 'noindex' in public_client.get(path+'?utm_source=x').text
    assert public_client.get('/guides/not-a-guide').status_code == 404
    assert public_client.get('/about').status_code == 200
    assert '/about' in sitemap and '/guides' in sitemap
    assert '30 minutes' in public_client.get('/privacy').text
