"""Compressed public snapshots preserve bytes and bind database defaults before imports."""

import asyncio
import gzip
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def fixture_database(path):
    from aggregator.db import init_db, upsert_deals
    from aggregator.models import AggregatedDeal
    from deal_common.offers import VariantOffer

    asyncio.run(init_db(path))
    observed_at = datetime.now(UTC).replace(tzinfo=None)
    url = 'https://merchant.example/products/ski'
    offer = VariantOffer('178', url + '?variant=178', 300, 1200,
                         size='178', availability='in_stock')
    deal = AggregatedDeal(None, 'Fixture Merchant', 'Atomic Test Skis', url, 300, 1200, 75,
                          'skis', '178cm', 178, 178, observed_at, offers=[offer])
    asyncio.run(upsert_deals([deal], path))
    with sqlite3.connect(path) as db:
        db.execute('INSERT INTO scrape_runs VALUES (?, ?, ?, ?, ?, ?)',
                   ('Fixture Merchant', observed_at.isoformat(), 'ok', 1, 0, 1))
        db.execute('INSERT INTO price_history VALUES (?, ?, ?)', (url, '2026-10-01T00:00:00', 400))
        db.execute('INSERT INTO offer_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (url, '178', '2026-10-01T00:00:00', 400, 1200, 'USD',
                    'in_stock', 'retailer_compare_at', deal.name))
    return observed_at.isoformat()


def manual_bundle(path):
    raw = path.read_bytes()
    compressed = path.with_name(path.name + '.gz')
    manifest = path.with_name(path.name + '.manifest.json')
    compressed.write_bytes(gzip.compress(raw, mtime=0))
    manifest.write_text(json.dumps({'version': 1, 'bytes': len(raw),
                                    'sha256': hashlib.sha256(raw).hexdigest()}))
    return compressed, manifest


def test_build_main_bundles_existing_snapshot_without_changing_source(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('snapshot_build_test', ROOT / 'scripts/vercel_build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    source = tmp_path / 'deals.db'
    fixture_database(source)
    original = source.read_bytes()
    monkeypatch.setattr(build, 'DB_DEST', source)
    monkeypatch.setattr(build, 'copy_static_assets', lambda: None)
    monkeypatch.setenv('VERCEL_SKIP_DB_DOWNLOAD', '1')
    assert build.main() == 0
    assert source.read_bytes() == original
    assert gzip.decompress(source.with_name('deals.db.gz').read_bytes()) == original
    manifest = json.loads(source.with_name('deals.db.manifest.json').read_text())
    assert manifest == {'version': 1, 'bytes': len(original),
                        'sha256': hashlib.sha256(original).hexdigest()}


@pytest.mark.parametrize('deployment', [False, True])
def test_entrypoint_extracts_before_database_defaults_import_and_serves_health(tmp_path, deployment):
    source = tmp_path / 'catalogs/fresh-powder/data/deals.db'
    source.parent.mkdir(parents=True)
    observed_at = fixture_database(source)
    original = source.read_bytes()
    manual_bundle(source)
    source.unlink()
    entrypoint = tmp_path / 'app.py'
    entrypoint.write_bytes((ROOT / 'app.py').read_bytes())
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
    env.update(
        PYTHONPATH=os.pathsep.join(str(ROOT / path) for path in ('common', 'catalogs/fresh-powder/src')),
        HOME=str(tmp_path), TMPDIR=str(runtime), DEALS_DB_READ_ONLY='0',
        PUBLIC_MODE='1', DISABLE_APP_LIFESPAN='1', AUTH_DB_PATH=str(tmp_path / 'unused-auth.db'),
        SECRET_KEY='offline-only-test-signing-key-at-least-32-characters',
    )
    if deployment:
        env['VERCEL'] = '1'
    code = '''
import asyncio, hashlib, json, os, runpy
from pathlib import Path
from fastapi.testclient import TestClient
entry = runpy.run_path(os.environ['SNAPSHOT_TEST_ENTRYPOINT'])
from aggregator import db
from aggregator.web.app import _deals_db_read_only_runtime
with TestClient(entry['app']) as client:
    response = client.get('/healthz')
print(json.dumps({'env_path': os.environ.get('DATABASE_PATH'), 'db_path': str(db.DB_PATH),
                  'read_only_flag': os.environ.get('DEALS_DB_READ_ONLY'),
                  'runtime_read_only': _deals_db_read_only_runtime(),
                  'count': asyncio.run(db.query_deals(count_only=True)),
                  'health_status': response.status_code, 'health': response.json(),
                  'sha256': hashlib.sha256(db.DB_PATH.read_bytes()).hexdigest()}))
'''
    env['SNAPSHOT_TEST_ENTRYPOINT'] = str(entrypoint)
    result = subprocess.run([sys.executable, '-c', code], env=env, text=True, capture_output=True,
                            timeout=30, check=True)
    data = json.loads(result.stdout)
    assert data['env_path'] == data['db_path']
    assert data['read_only_flag'] == '1' and data['runtime_read_only']
    assert Path(data['db_path']).is_relative_to(runtime)
    assert data['sha256'] == hashlib.sha256(original).hexdigest()
    assert data['count'] == 1
    assert data['health_status'] == 200 and data['health']['status'] == 'ok'
    assert data['health']['checked_at'] == observed_at
    assert not (tmp_path / 'unused-auth.db').exists()


def test_deterministic_bundle_roundtrip_preserves_every_history_row(tmp_path):
    from aggregator.bundled_snapshot import (
        materialize_snapshot_bundle,
        write_snapshot_bundle,
    )

    source = tmp_path / 'deals.db'
    fixture_database(source)
    original = source.read_bytes()
    identity = write_snapshot_bundle(source)
    archive = source.with_name('deals.db.gz')
    manifest = source.with_name('deals.db.manifest.json')
    first_archive, first_manifest = archive.read_bytes(), manifest.read_bytes()
    assert write_snapshot_bundle(source) == identity
    assert (archive.read_bytes(), manifest.read_bytes()) == (first_archive, first_manifest)
    target = materialize_snapshot_bundle(archive, manifest, cache_dir=tmp_path / 'runtime')
    assert target != source and target.read_bytes() == original
    assert source.read_bytes() == original
    with sqlite3.connect(f'file:{target}?mode=ro', uri=True) as db:
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        for table, expected in [('deals', 1), ('deal_offers', 1), ('price_history', 2),
                                ('offer_observations', 2), ('scrape_runs', 1)]:
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone() == (expected,)
        with pytest.raises(sqlite3.OperationalError, match='readonly'):
            db.execute('DELETE FROM price_history')


def test_verified_cache_is_reused_and_same_size_corrupt_cache_is_rebuilt(tmp_path, monkeypatch):
    import aggregator.bundled_snapshot as module

    source = tmp_path / 'deals.db'
    fixture_database(source)
    archive, manifest = manual_bundle(source)
    cache = tmp_path / 'cache'
    target = module.materialize_snapshot_bundle(archive, manifest, cache_dir=cache)
    modified = target.stat().st_mtime_ns
    original_open = module.gzip.open

    def must_not_decompress(*args, **kwargs):
        raise AssertionError('Verified bytes should be reused')

    monkeypatch.setattr(module.gzip, 'open', must_not_decompress)
    assert module.materialize_snapshot_bundle(archive, manifest, cache_dir=cache) == target
    assert target.stat().st_mtime_ns == modified
    monkeypatch.setattr(module.gzip, 'open', original_open)
    target.chmod(0o644)
    target.write_bytes(b'x' * target.stat().st_size)
    assert module.materialize_snapshot_bundle(archive, manifest, cache_dir=cache) == target
    assert target.read_bytes() == source.read_bytes()
    assert list(cache.glob('*.tmp')) == []


@pytest.mark.parametrize('damage', ['truncated', 'not-gzip', 'wrong-size', 'wrong-sha', 'extra-bytes'])
def test_invalid_bundle_never_publishes_partial_database_or_leaves_temp(tmp_path, damage):
    from aggregator.bundled_snapshot import materialize_snapshot_bundle

    source = tmp_path / 'deals.db'
    fixture_database(source)
    original = source.read_bytes()
    archive, manifest = manual_bundle(source)
    previous_cache = tmp_path / 'previous'
    previous = materialize_snapshot_bundle(archive, manifest, cache_dir=previous_cache)
    identity = json.loads(manifest.read_text())
    if damage == 'truncated':
        archive.write_bytes(archive.read_bytes()[:-10])
    elif damage == 'not-gzip':
        archive.write_bytes(b'not a gzip archive')
    elif damage == 'wrong-size':
        identity['bytes'] -= 1
        manifest.write_text(json.dumps(identity))
    elif damage == 'wrong-sha':
        identity['sha256'] = '0' * 64
        manifest.write_text(json.dumps(identity))
    else:
        archive.write_bytes(gzip.compress(original + b'extra', mtime=0))
    cache = tmp_path / 'broken-runtime'
    with pytest.raises(RuntimeError, match='snapshot'):
        materialize_snapshot_bundle(archive, manifest, cache_dir=cache)
    assert list(cache.glob('*.db')) == []
    assert list(cache.glob('*.tmp')) == []
    assert previous.read_bytes() == original
    assert source.read_bytes() == original


@pytest.mark.parametrize('change', [
    {'version': 2}, {'bytes': True}, {'bytes': -1}, {'sha256': '../not-a-digest'}, {'extra': 1},
])
def test_invalid_manifest_cannot_choose_a_runtime_destination(tmp_path, change):
    from aggregator.bundled_snapshot import materialize_snapshot_bundle

    source = tmp_path / 'deals.db'
    fixture_database(source)
    archive, manifest = manual_bundle(source)
    identity = json.loads(manifest.read_text())
    identity.update(change)
    manifest.write_text(json.dumps(identity))
    cache = tmp_path / 'runtime'
    with pytest.raises(RuntimeError, match='manifest'):
        materialize_snapshot_bundle(archive, manifest, cache_dir=cache)
    assert not cache.exists()


def test_concurrent_materialization_atomically_publishes_only_verified_bytes(tmp_path, monkeypatch):
    from threading import Barrier, local

    import aggregator.bundled_snapshot as module

    source = tmp_path / 'deals.db'
    fixture_database(source)
    original = source.read_bytes()
    archive, manifest = manual_bundle(source)
    cache = tmp_path / 'runtime'
    barrier = Barrier(6)
    original_open, original_replace = module.gzip.open, module.os.replace
    original_matches = module._matches
    thread_state = local()
    published, opened = [], []

    def synchronized_initial_check(*args):
        matched = original_matches(*args)
        if not getattr(thread_state, 'checked', False):
            thread_state.checked = True
            barrier.wait(timeout=10)
        return matched

    def counted_open(*args, **kwargs):
        opened.append(args[0])
        assert len(list(cache.glob('*.tmp'))) == 1
        return original_open(*args, **kwargs)

    def checked_replace(source_path, destination_path):
        assert Path(source_path).read_bytes() == original
        if Path(destination_path).exists():
            assert Path(destination_path).read_bytes() == original
        original_replace(source_path, destination_path)
        published.append(str(destination_path))

    monkeypatch.setattr(module, '_matches', synchronized_initial_check)
    monkeypatch.setattr(module.gzip, 'open', counted_open)
    monkeypatch.setattr(module.os, 'replace', checked_replace)
    with ThreadPoolExecutor(max_workers=6) as workers:
        results = list(workers.map(
            lambda _: module.materialize_snapshot_bundle(archive, manifest, cache_dir=cache), range(6)))
    assert len(set(results)) == 1
    assert len(published) == 1 and len(opened) == 1
    assert results[0].read_bytes() == original
    assert list(cache.glob('*.tmp')) == []


def test_interrupted_extraction_is_cleaned_only_under_its_digest_lock(tmp_path):
    from aggregator.bundled_snapshot import materialize_snapshot_bundle

    source = tmp_path / 'deals.db'
    fixture_database(source)
    archive, manifest = manual_bundle(source)
    identity = json.loads(manifest.read_text())
    cache = tmp_path / 'runtime'
    cache.mkdir()
    abandoned = cache / f".snapshot-{identity['sha256']}-interrupted.db.tmp"
    abandoned.write_bytes(b'abandoned partial snapshot')
    unrelated = cache / ('.snapshot-' + '0' * 64 + '-other.db.tmp')
    unrelated.write_bytes(b'another digest owns this temporary')
    previous = cache / ('deals-' + '0' * 64 + '.db')
    previous.write_bytes(b'previous snapshot cache')

    target = materialize_snapshot_bundle(archive, manifest, cache_dir=cache)

    assert target.read_bytes() == source.read_bytes()
    assert not abandoned.exists()
    assert unrelated.read_bytes() == b'another digest owns this temporary'
    assert previous.read_bytes() == b'previous snapshot cache'
    assert list(cache.glob(f".snapshot-{identity['sha256']}-*.db.tmp")) == []


def test_explicit_database_path_wins_even_with_invalid_bundle(tmp_path, monkeypatch):
    import aggregator.bundled_snapshot as module

    explicit = tmp_path / 'explicit.db'
    monkeypatch.setenv('DATABASE_PATH', str(explicit))
    monkeypatch.setenv('VERCEL', '1')
    monkeypatch.setenv('DEALS_DB_READ_ONLY', '0')

    def forbidden(*args, **kwargs):
        raise AssertionError('Explicit database path must not inspect bundled artifacts')

    monkeypatch.setattr(module, 'materialize_snapshot_bundle', forbidden)
    assert module.configure_runtime_snapshot(tmp_path) == explicit
    assert os.environ['DATABASE_PATH'] == str(explicit)
    assert os.environ['DEALS_DB_READ_ONLY'] == '0'
    assert not explicit.exists()


def test_uncompressed_local_database_keeps_local_behavior(tmp_path, monkeypatch):
    from aggregator.bundled_snapshot import configure_runtime_snapshot

    source = tmp_path / 'catalogs/fresh-powder/data/deals.db'
    source.parent.mkdir(parents=True)
    fixture_database(source)
    source.with_name('deals.db.gz').write_bytes(b'invalid leftover archive')
    monkeypatch.delenv('DATABASE_PATH', raising=False)
    monkeypatch.delenv('VERCEL', raising=False)
    monkeypatch.setenv('DEALS_DB_READ_ONLY', '0')
    assert configure_runtime_snapshot(tmp_path) == source
    assert 'DATABASE_PATH' not in os.environ
    assert os.environ['DEALS_DB_READ_ONLY'] == '0'


def test_vercel_missing_bundle_fails_before_database_defaults_can_bind(tmp_path, monkeypatch):
    from aggregator.bundled_snapshot import configure_runtime_snapshot

    monkeypatch.delenv('DATABASE_PATH', raising=False)
    monkeypatch.setenv('VERCEL', '1')
    with pytest.raises(RuntimeError, match='manifest'):
        configure_runtime_snapshot(tmp_path)
    assert 'DATABASE_PATH' not in os.environ


def test_deployment_includes_compressed_artifacts_and_excludes_plain_database():
    config = json.loads((ROOT / 'vercel.json').read_text())['functions']['api/index.py']
    assert 'catalogs/fresh-powder/data/deals.db.gz' in config['includeFiles']
    assert 'catalogs/fresh-powder/data/deals.db.manifest.json' in config['includeFiles']
    assert 'catalogs/fresh-powder/data/deals.db,' in config['excludeFiles']


def test_failed_compression_keeps_previous_bundle_and_source_bytes(tmp_path, monkeypatch):
    import aggregator.bundled_snapshot as module

    source = tmp_path / 'deals.db'
    fixture_database(source)
    original = source.read_bytes()
    module.write_snapshot_bundle(source)
    archive = source.with_name('deals.db.gz')
    manifest = source.with_name('deals.db.manifest.json')
    previous = archive.read_bytes(), manifest.read_bytes()

    def broken_writer(*args, **kwargs):
        kwargs['fileobj'].write(b'partial compressed data')
        raise OSError('Injected compression failure')

    monkeypatch.setattr(module.gzip, 'GzipFile', broken_writer)
    with pytest.raises(OSError, match='Injected compression failure'):
        module.write_snapshot_bundle(source)
    assert (archive.read_bytes(), manifest.read_bytes()) == previous
    assert source.read_bytes() == original
    assert list(tmp_path.glob('*.tmp')) == []
