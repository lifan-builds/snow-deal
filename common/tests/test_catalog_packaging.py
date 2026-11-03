from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from deal_common.catalog.storage import save_source
from tool_deals.catalog import CATALOG

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("package_catalog", ROOT / "scripts/package_catalog.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


def snapshot(path, *, catalog="tools", timestamp=None):
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    product = dict(name="Fixture Table Saw", url="https://www.woodcraft.com/products/fixture", brand="Fixture",
                   category="Workshop equipment", format="Not specified", platform="", offers=[dict(
                       variant_key="1", url="https://www.woodcraft.com/products/fixture?variant=1",
                       current_price=500, original_price=1000, size=None, options="", availability="in_stock",
                       image_url=None, reference_basis="retailer_compare_at")])
    save_source(path, catalog, "Woodcraft", timestamp, [product], "complete", {})
    for source in CATALOG.sources:
        if source.name != "Woodcraft":
            save_source(path, catalog, source.name, timestamp, [], "complete", {})


def test_standalone_bundle_contains_only_selected_catalog_and_serves(tmp_path):
    db = tmp_path / "tools.db"
    snapshot(db, timestamp=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat())
    snapshot(db)
    output = tmp_path / "bundle"
    receipt = packager.package("tools", db, output, "https://benchdrop.example.com")
    assert receipt["matching_deals"] == 1
    assert (output / "src/tool_deals/catalog.py").exists()
    assert not (output / "src/cycling_deals").exists()
    assert not list(output.rglob(".env*"))
    assert json.loads((output / "vercel.json").read_text())["rewrites"][0]["destination"] == "/api/index.py"
    result = subprocess.run([sys.executable, "-c", """
from api.index import app
from fastapi.testclient import TestClient
client = TestClient(app)
assert 'Fixture Table Saw' in client.get('/').text
assert 'https://benchdrop.example.com/' in client.get('/sitemap.xml').text
assert 'Disallow: /\\n' not in client.get('/robots.txt').text
assert 'X-Robots-Tag' not in client.get('/').headers
assert 'noindex' in client.get('/?q=Fixture').headers['X-Robots-Tag']
assert client.get('/static/catalog.css').status_code == 200
assert client.get('/healthz').json()['catalog'] == 'tools'
import json
from pathlib import Path
assert client.get('/healthz').json()['snapshot_sha256'] == json.loads(Path('BUILD-RECEIPT.json').read_text())['snapshot_sha256']
history = client.get('/history', params={'source':'Woodcraft','product':'https://www.woodcraft.com/products/fixture','variant':'1'})
assert history.status_code == 200 and '2 observed days' in history.text
"""], cwd=output, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("reason", ["stale", "wrong_catalog", "missing", "empty"])
def test_package_rejects_bad_snapshot_before_writing(tmp_path, reason):
    db = tmp_path / "tools.db"
    if reason != "missing":
        snapshot(db, catalog="cycling" if reason == "wrong_catalog" else "tools",
                 timestamp=(datetime.now(timezone.utc) - timedelta(days=4)).isoformat() if reason == "stale" else None)
    if reason == "empty":
        save_source(db, "tools", "Woodcraft", datetime.now(timezone.utc).isoformat(), [], "complete", {})
    output = tmp_path / "bundle"
    with pytest.raises(ValueError):
        packager.package("tools", db, output)
    assert not output.exists()
