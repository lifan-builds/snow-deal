import hashlib
import importlib.util
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from deal_common.catalog.storage import read_sources, save_source

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('restore_catalog', ROOT / 'scripts/restore_catalog.py')
restore_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore_module)


def asset(name, body):
    return {'name': name, 'state': 'uploaded', 'size': len(body),
            'digest': 'sha256:' + hashlib.sha256(body).hexdigest()}


def snapshot(path, *, include_current=True):
    now = datetime(2026, 11, 5, 12, tzinfo=UTC)
    product = {'name': 'Drill', 'url': 'https://example.test/products/drill', 'brand': 'Maker',
               'category': 'Power tools', 'source_category': 'Drills', 'format': 'Not specified', 'platform': '',
               'offers': [{'variant_key': '42', 'url': 'https://example.test/products/drill?variant=42',
                           'current_price': 120, 'original_price': 200, 'size': None, 'options': '',
                           'availability': 'unknown', 'availability_note': 'Retailer shipping estimate'}]}
    save_source(path, 'tools', 'Woodcraft', (now - timedelta(days=1)).isoformat(), [product], 'complete', {})
    if include_current:
        product['offers'][0].update(current_price=100, availability='in_stock', availability_note='')
        save_source(path, 'tools', 'Woodcraft', now.isoformat(), [product], 'complete', {})
    return path.read_bytes()


@pytest.mark.parametrize('assets', [[], [{'name': 'cycling.db'}]])
def test_missing_history_requires_explicit_bootstrap(tmp_path, assets):
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'assets': assets}))
    destination = tmp_path / 'new.db'
    with pytest.raises(ValueError, match='bootstrap'):
        restore_module.restore('tools', destination, transport=transport)
    assert restore_module.restore('tools', destination, bootstrap=True, transport=transport) == 'explicit-bootstrap'
    assert not destination.exists()


@pytest.mark.parametrize('phase', ['metadata', 'asset'])
def test_failed_download_never_becomes_bootstrap(tmp_path, phase):
    body = snapshot(tmp_path / 'valid.db')
    def handler(request):
        if phase == 'asset' and str(request.url) == restore_module.RELEASE_API:
            return httpx.Response(200, json={'assets': [asset('tools.db', body)]})
        return httpx.Response(503)
    with pytest.raises(httpx.HTTPStatusError):
        restore_module.restore('tools', tmp_path / 'new.db', bootstrap=True, transport=httpx.MockTransport(handler))


def test_restore_preserves_history_and_rejects_wrong_catalog(tmp_path):
    previous = tmp_path / 'previous.db'
    save_source(previous, 'tools', 'Woodcraft', datetime.now(UTC).isoformat(), [], 'complete', {})
    body = previous.read_bytes()
    def handler(request):
        if request.url.host == 'api.github.com':
            return httpx.Response(200, json={'assets':[asset('tools.db', body), asset('cycling.db', body)]})
        return httpx.Response(200, content=body)
    transport = httpx.MockTransport(handler)
    destination = tmp_path / 'restored.db'
    assert restore_module.restore('tools', destination, transport=transport) == 'restored'
    assert read_sources(destination, 'tools')[0]['name'] == 'Woodcraft'
    bad = tmp_path / 'wrong.db'
    with pytest.raises(ValueError, match='different catalog'):
        restore_module.restore('cycling', bad, transport=transport)
    assert not bad.exists()
    with pytest.raises(ValueError, match='overwrite'):
        restore_module.restore('tools', destination, transport=transport)


def test_metadata_auth_never_reaches_asset_or_redirect(tmp_path):
    previous = tmp_path / 'previous.db'
    save_source(previous, 'tools', 'Woodcraft', datetime.now(UTC).isoformat(), [], 'complete', {})
    body = previous.read_bytes()
    visited = []

    def handler(request):
        visited.append(request.url.host)
        if str(request.url) == restore_module.RELEASE_API:
            assert request.headers['Authorization'] == 'Bearer test-only-token'
            return httpx.Response(200, json={'assets': [asset('tools.db', body)]})
        assert 'Authorization' not in request.headers
        if request.url.host == 'github.com':
            return httpx.Response(302, headers={'Location': 'https://release-assets.githubusercontent.com/example.db'})
        return httpx.Response(200, content=body)

    destination = tmp_path / 'restored.db'
    assert restore_module.restore('tools', destination, github_token='test-only-token',
                                  transport=httpx.MockTransport(handler)) == 'restored'
    assert visited == ['api.github.com', 'github.com', 'release-assets.githubusercontent.com']
    assert read_sources(destination, 'tools')[0]['name'] == 'Woodcraft'


@pytest.mark.parametrize('status', [302, 403, 429])
def test_metadata_redirect_or_rate_limit_never_discards_history(tmp_path, status):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(status, headers={'Location': 'https://example.test/metadata'})

    destination = tmp_path / 'restored.db'
    with pytest.raises(httpx.HTTPStatusError):
        restore_module.restore('tools', destination, bootstrap=True, github_token='test-only-token',
                               transport=httpx.MockTransport(handler))
    assert len(requests) == 1
    assert not destination.exists()


@pytest.mark.parametrize('uppercase_digest', [False, True])
def test_verified_asset_restores_exact_bytes_and_all_history(tmp_path, uppercase_digest):
    body = snapshot(tmp_path / 'current.db')
    metadata = asset('tools.db', body)
    if uppercase_digest:
        metadata['digest'] = 'sha256:' + metadata['digest'][7:].upper()
    class Chunks(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(0, len(body), 113):
                yield body[index:index+113]
    def handler(request):
        if str(request.url) == restore_module.RELEASE_API:
            return httpx.Response(200, json={'assets': [metadata]})
        return httpx.Response(200, stream=Chunks())
    destination = tmp_path / 'restore' / 'tools.db'
    assert restore_module.restore('tools', destination, transport=httpx.MockTransport(handler)) == 'restored'
    assert destination.read_bytes() == body
    with sqlite3.connect(destination) as db:
        history = db.execute('SELECT observed_at, products FROM observations ORDER BY observed_at').fetchall()
    assert len(history) == 2 and 'Retailer shipping estimate' in history[0][1]
    assert read_sources(destination, 'tools')[0]['successful_at'] == '2026-11-05T12:00:00+00:00'
    assert list(destination.parent.iterdir()) == [destination]


@pytest.mark.parametrize('bootstrap', [False, True])
@pytest.mark.parametrize('kind', ['stale-history', 'same-sized-change'])
def test_valid_stale_or_same_sized_changed_sqlite_cannot_match_current_metadata(tmp_path, bootstrap, kind):
    body = snapshot(tmp_path / 'current.db')
    changed = tmp_path / 'changed.db'
    if kind == 'stale-history':
        downloaded = snapshot(changed, include_current=False)
    else:
        changed.write_bytes(body)
        with sqlite3.connect(changed) as db:
            db.execute('UPDATE sources SET detail=?', ('{"changed":true}',))
        downloaded = changed.read_bytes()
        assert len(downloaded) == len(body)
    with sqlite3.connect(changed) as db:
        assert db.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    assert downloaded != body
    def handler(request):
        if str(request.url) == restore_module.RELEASE_API:
            return httpx.Response(200, json={'assets': [asset('tools.db', body)]})
        return httpx.Response(200, content=downloaded)
    destination = tmp_path / 'restore' / 'tools.db'
    with pytest.raises(ValueError):
        restore_module.restore('tools', destination, bootstrap=bootstrap, transport=httpx.MockTransport(handler))
    assert not destination.exists() and list(destination.parent.iterdir()) == []


@pytest.mark.parametrize('bootstrap', [False, True])
@pytest.mark.parametrize('change', [
    {'omit': 'state'}, {'state': None}, {'state': 'starter'}, {'state': 'uploaded '},
    {'omit': 'size'}, {'size': None}, {'size': True}, {'size': False}, {'size': 0}, {'size': -1},
    {'size': 1.5}, {'size': '100'}, {'size': restore_module.MAX_BYTES + 1},
    {'omit': 'digest'}, {'digest': None}, {'digest': True}, {'digest': 12}, {'digest': ''},
    {'digest': 'sha256:' + 'a' * 63}, {'digest': 'sha256:' + 'a' * 65},
    {'digest': 'sha256:' + 'g' * 64}, {'digest': 'sha512:' + 'a' * 64},
    {'digest': 'SHA256:' + 'a' * 64}, {'digest': 'sha256:' + 'a' * 64 + '\n'},
])
def test_bad_selected_asset_metadata_fails_before_asset_request_or_destination_setup(tmp_path, bootstrap, change):
    body = snapshot(tmp_path / 'valid.db')
    metadata = asset('tools.db', body)
    if 'omit' in change:
        metadata.pop(change['omit'])
    else:
        metadata.update(change)
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, json={'assets': [metadata]}) if str(request.url) == restore_module.RELEASE_API else httpx.Response(200, content=body)
    destination = tmp_path / 'not-created' / 'tools.db'
    with pytest.raises(ValueError):
        restore_module.restore('tools', destination, bootstrap=bootstrap, transport=httpx.MockTransport(handler))
    assert requests == [restore_module.RELEASE_API]
    assert not destination.parent.exists()


@pytest.mark.parametrize('metadata', [None, [], {'assets': None}, {'assets': {}}, {'assets': [None]},
                                     {'assets': ['tools.db']}, {'assets': [{}]}, {'assets': [{'name': None}]}])
def test_malformed_metadata_cannot_authorize_bootstrap(tmp_path, metadata):
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, content=json.dumps(metadata), headers={'Content-Type': 'application/json'})
    destination = tmp_path / 'not-created' / 'tools.db'
    with pytest.raises(ValueError):
        restore_module.restore('tools', destination, bootstrap=True, transport=httpx.MockTransport(handler))
    assert requests == [restore_module.RELEASE_API] and not destination.parent.exists()


def test_duplicate_named_assets_are_not_a_pinned_snapshot(tmp_path):
    body = snapshot(tmp_path / 'valid.db')
    metadata = asset('tools.db', body)
    requests = []
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200, json={'assets': [metadata, metadata]})
    destination = tmp_path / 'not-created' / 'tools.db'
    with pytest.raises(ValueError):
        restore_module.restore('tools', destination, bootstrap=True, transport=httpx.MockTransport(handler))
    assert requests == [restore_module.RELEASE_API] and not destination.parent.exists()


@pytest.mark.parametrize('bootstrap', [False, True])
@pytest.mark.parametrize('change', ['short', 'excess', 'wrong-digest'])
def test_stream_identity_failure_happens_before_sqlite_and_cleans_partial_temp(tmp_path, monkeypatch, bootstrap, change):
    body = snapshot(tmp_path / 'valid.db')
    metadata = asset('tools.db', body)
    chunks = [body[:100], body[100:]]
    if change == 'short':
        chunks[-1] = chunks[-1][:-1]
    elif change == 'excess':
        chunks += [b'excess', b'not-read-after-limit']
    else:
        metadata['digest'] = 'sha256:' + '0' * 64
    consumed = []
    class Chunks(httpx.SyncByteStream):
        def __iter__(self):
            for chunk in chunks:
                consumed.append(chunk)
                yield chunk
    def handler(request):
        if str(request.url) == restore_module.RELEASE_API:
            return httpx.Response(200, json={'assets': [metadata]})
        return httpx.Response(200, stream=Chunks())
    def unverified_sqlite(*args, **kwargs):
        raise AssertionError('Unverified bytes were opened as SQLite')
    monkeypatch.setattr(restore_module.sqlite3, 'connect', unverified_sqlite)
    destination = tmp_path / 'restore' / 'tools.db'
    with pytest.raises(ValueError):
        restore_module.restore('tools', destination, bootstrap=bootstrap, transport=httpx.MockTransport(handler))
    assert not destination.exists() and list(destination.parent.iterdir()) == []
    if change == 'excess':
        assert consumed[-1] == b'excess'


def test_matching_metadata_does_not_bypass_sqlite_validation(tmp_path):
    body = b'This is not a SQLite database.'
    def handler(request):
        if str(request.url) == restore_module.RELEASE_API:
            return httpx.Response(200, json={'assets': [asset('tools.db', body)]})
        return httpx.Response(200, content=body)
    destination = tmp_path / 'restore' / 'tools.db'
    with pytest.raises(sqlite3.DatabaseError):
        restore_module.restore('tools', destination, bootstrap=True, transport=httpx.MockTransport(handler))
    assert not destination.exists() and list(destination.parent.iterdir()) == []
