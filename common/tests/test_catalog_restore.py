from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import httpx
import pytest

from deal_common.catalog.storage import save_source, read_sources

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('restore_catalog', ROOT / 'scripts/restore_catalog.py')
restore_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore_module)


def test_missing_history_requires_explicit_bootstrap(tmp_path):
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={'assets':[]}))
    destination = tmp_path / 'new.db'
    with pytest.raises(ValueError, match='bootstrap'):
        restore_module.restore('tools', destination, transport=transport)
    assert restore_module.restore('tools', destination, bootstrap=True, transport=transport) == 'explicit-bootstrap'
    assert not destination.exists()


def test_failed_download_never_becomes_bootstrap(tmp_path):
    def handler(request):
        return httpx.Response(503)
    with pytest.raises(httpx.HTTPStatusError):
        restore_module.restore('tools', tmp_path / 'new.db', bootstrap=True, transport=httpx.MockTransport(handler))


def test_restore_preserves_history_and_rejects_wrong_catalog(tmp_path):
    previous = tmp_path / 'previous.db'
    save_source(previous, 'tools', 'Woodcraft', datetime.now(timezone.utc).isoformat(), [], 'complete', {})
    body = previous.read_bytes()
    def handler(request):
        if request.url.host == 'api.github.com':
            return httpx.Response(200, json={'assets':[{'name':'tools.db'}, {'name':'cycling.db'}]})
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
    save_source(previous, 'tools', 'Woodcraft', datetime.now(timezone.utc).isoformat(), [], 'complete', {})
    body = previous.read_bytes()
    visited = []

    def handler(request):
        visited.append(request.url.host)
        if str(request.url) == restore_module.RELEASE_API:
            assert request.headers['Authorization'] == 'Bearer test-only-token'
            return httpx.Response(200, json={'assets': [{'name': 'tools.db'}]})
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
