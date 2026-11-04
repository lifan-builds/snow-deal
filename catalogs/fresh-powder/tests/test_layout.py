"""Exercise moved build assets and the root deployment entrypoint offline."""

import importlib.util
import io
import sqlite3
from pathlib import Path

import pytest
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
    original = db.read_bytes()
    build.download_deals_db()
    assert build.validate_sqlite_db(db) == (1, '2026-11-02T00:00:00')
    assert db.read_bytes() == original


def test_download_compacts_only_temporary_snapshot_and_preserves_history(tmp_path, monkeypatch):
    from aggregator import db as db_module
    from aggregator import reviews

    build = load_module('vercel_build_compaction_test', ROOT / 'scripts/vercel_build.py')
    source = tmp_path / 'public-snapshot.db'
    with sqlite3.connect(source) as conn:
        conn.executescript('''
            CREATE TABLE deals (id INTEGER PRIMARY KEY AUTOINCREMENT, scraped_at TEXT);
            CREATE TABLE price_history (url TEXT, observed_at TEXT, price REAL,
                                        PRIMARY KEY (url, observed_at));
            CREATE TABLE offer_observations (variant_key TEXT, observed_at TEXT, price REAL,
                                             PRIMARY KEY (variant_key, observed_at));
            CREATE INDEX idx_history_url ON price_history(url);
            CREATE TABLE temporary_padding (value BLOB);
        ''')
        conn.executemany('INSERT INTO deals(scraped_at) VALUES (?)',
                         [('2026-11-02T00:00:00',), ('2026-11-04T13:25:58.343623',)])
        conn.executemany('INSERT INTO price_history VALUES (?, ?, ?)',
                         [('https://merchant.example/ski', '2026-11-02T00:00:00', 499.95),
                          ('https://merchant.example/ski', '2026-11-04T13:25:58.343623', 399.95)])
        conn.executemany('INSERT INTO offer_observations VALUES (?, ?, ?)',
                         [('size178', '2026-11-02T00:00:00', 499.95),
                          ('size178', '2026-11-04T13:25:58.343623', 399.95)])
        conn.executemany('INSERT INTO temporary_padding VALUES (?)', [(b'x' * 4096,)] * 300)
        conn.execute('DROP TABLE temporary_padding')
    original = source.read_bytes()
    destination = tmp_path / 'build/deals.db'
    monkeypatch.setattr(build, 'DB_DEST', destination)
    monkeypatch.delenv('VERCEL_SKIP_DB_DOWNLOAD', raising=False)
    monkeypatch.setenv('DEALS_DB_DOWNLOAD_URL', 'https://snapshot.example/deals.db')
    monkeypatch.setattr(build, 'urlopen', lambda url, timeout: io.BytesIO(original))

    # This test isolates physical compaction from the separate category/review
    # migrations. Each still receives the temporary download, before replacement.
    visited = []
    async def no_change(path):
        visited.append(path)
        assert path.parent == destination.parent and path != destination
        return 0
    monkeypatch.setattr(db_module, 'init_db', no_change)
    monkeypatch.setattr(db_module, 'repair_deal_categories', no_change)
    monkeypatch.setattr(reviews, 'compute_and_store_deal_reviews', no_change)
    build.download_deals_db()
    assert len(visited) == 3 and len(set(visited)) == 1
    assert destination.stat().st_size < len(original)
    assert source.read_bytes() == original
    assert build.validate_sqlite_db(destination) == (2, '2026-11-04T13:25:58.343623')
    with sqlite3.connect(destination) as conn:
        conn.execute('ATTACH DATABASE ? AS previous', (str(source),))
        assert conn.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
        assert conn.execute('PRAGMA freelist_count').fetchone()[0] == 0
        assert conn.execute('SELECT type, name, tbl_name, sql FROM main.sqlite_schema EXCEPT '
                            'SELECT type, name, tbl_name, sql FROM previous.sqlite_schema').fetchall() == []
        assert conn.execute('SELECT type, name, tbl_name, sql FROM previous.sqlite_schema EXCEPT '
                            'SELECT type, name, tbl_name, sql FROM main.sqlite_schema').fetchall() == []
        for table in ('deals', 'price_history', 'offer_observations', 'sqlite_sequence'):
            assert conn.execute(f'SELECT COUNT(*) FROM main.{table}').fetchone() == conn.execute(
                f'SELECT COUNT(*) FROM previous.{table}').fetchone()
            assert conn.execute(f'SELECT * FROM main.{table} EXCEPT SELECT * FROM previous.{table}').fetchall() == []
            assert conn.execute(f'SELECT * FROM previous.{table} EXCEPT SELECT * FROM main.{table}').fetchall() == []


def test_compaction_failure_keeps_previous_bundle_and_removes_temporary_download(tmp_path, monkeypatch):
    from aggregator import db as db_module
    from aggregator import reviews

    build = load_module('vercel_build_failure_test', ROOT / 'scripts/vercel_build.py')
    source = tmp_path / 'public-snapshot.db'
    destination = tmp_path / 'build/deals.db'
    destination.parent.mkdir()
    for path, observed_at in ((source, '2026-11-04'), (destination, '2026-11-02')):
        with sqlite3.connect(path) as conn:
            conn.execute('CREATE TABLE deals (scraped_at TEXT)')
            conn.execute('INSERT INTO deals VALUES (?)', (observed_at,))
    original_source, previous_bundle = source.read_bytes(), destination.read_bytes()
    monkeypatch.setattr(build, 'DB_DEST', destination)
    monkeypatch.delenv('VERCEL_SKIP_DB_DOWNLOAD', raising=False)
    monkeypatch.setenv('DEALS_DB_DOWNLOAD_URL', 'https://snapshot.example/deals.db')
    monkeypatch.setattr(build, 'urlopen', lambda url, timeout: io.BytesIO(original_source))

    async def no_change(path):
        return 0
    monkeypatch.setattr(db_module, 'init_db', no_change)
    monkeypatch.setattr(db_module, 'repair_deal_categories', no_change)
    monkeypatch.setattr(reviews, 'compute_and_store_deal_reviews', no_change)
    compact = build.compact_downloaded_db

    def fail_after_compaction(path):
        compact(path)
        raise RuntimeError('Injected failure before publishing compacted snapshot')
    monkeypatch.setattr(build, 'compact_downloaded_db', fail_after_compaction)
    with pytest.raises(RuntimeError, match='Injected failure'):
        build.download_deals_db()
    assert destination.read_bytes() == previous_bundle
    assert source.read_bytes() == original_source
    assert list(destination.parent.glob('deals.*.db')) == []


def test_root_entrypoint_loads_fresh_powder_static_assets(monkeypatch):
    monkeypatch.setenv('DISABLE_APP_LIFESPAN', '1')
    monkeypatch.setenv('PUBLIC_MODE', '1')
    entrypoint = load_module('deployment_entrypoint_test', ROOT / 'app.py')
    with TestClient(entrypoint.app) as client:
        assert client.get('/static/style.css').status_code == 200
        assert client.get('/static/img/favicon.ico').status_code == 200
        assert client.get('/robots.txt').status_code == 200
    assert entrypoint.app.title == 'FreshPowder'
