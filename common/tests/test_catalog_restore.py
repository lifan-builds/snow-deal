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
