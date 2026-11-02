"""Exercise moved build assets and the root deployment entrypoint offline."""

import importlib.util
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_copies_catalog_assets_and_checks_only_fixture_database(tmp_path, monkeypatch):
    build = load_module('vercel_build_test', ROOT / 'scripts/vercel_build.py')
    monkeypatch.setattr(build, 'ROOT', tmp_path)
    monkeypatch.setattr(build, 'STATIC_DEST', tmp_path / 'public/static')
    build.copy_static_assets()
    assert (build.STATIC_DEST / 'style.css').read_bytes() == (build.STATIC_SRC / 'style.css').read_bytes()
    assert (build.STATIC_DEST / 'img/favicon.ico').is_file()
    db = tmp_path / 'fixture.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE deals (scraped_at TEXT)')
        conn.execute("INSERT INTO deals VALUES ('2026-11-02T00:00:00')")
    monkeypatch.setattr(build, 'DB_DEST', db)
    monkeypatch.setenv('VERCEL_SKIP_DB_DOWNLOAD', '1')
    build.download_deals_db()
    assert build.validate_sqlite_db(db) == (1, '2026-11-02T00:00:00')


def test_root_entrypoint_loads_fresh_powder_static_assets(monkeypatch):
    monkeypatch.setenv('DISABLE_APP_LIFESPAN', '1')
    monkeypatch.setenv('PUBLIC_MODE', '1')
    entrypoint = load_module('deployment_entrypoint_test', ROOT / 'app.py')
    with TestClient(entrypoint.app) as client:
        assert client.get('/static/style.css').status_code == 200
        assert client.get('/static/img/favicon.ico').status_code == 200
        assert client.get('/robots.txt').status_code == 200
    assert entrypoint.app.title == 'FreshPowder'
