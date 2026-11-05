"""Package the public deal snapshot and materialize verified runtime bytes."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import tempfile
import zlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def write_snapshot_bundle(source: Path) -> dict:
    """Write deterministic compressed artifacts without changing the source DB."""
    archive = source.with_name(source.name + '.gz')
    manifest = source.with_name(source.name + '.manifest.json')
    temporary = []
    try:
        digest, size = hashlib.sha256(), 0
        with source.open('rb') as incoming, tempfile.NamedTemporaryFile(
                dir=source.parent, prefix='.snapshot-', suffix='.gz.tmp', delete=False) as outgoing:
            temporary.append(Path(outgoing.name))
            with gzip.GzipFile(filename='', mode='wb', fileobj=outgoing, mtime=0) as encoded:
                while block := incoming.read(CHUNK_SIZE):
                    size += len(block)
                    digest.update(block)
                    encoded.write(block)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if size == 0:
            raise RuntimeError('Cannot bundle an empty deal snapshot')
        identity = {'version': 1, 'bytes': size, 'sha256': digest.hexdigest()}
        with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=source.parent,
                prefix='.snapshot-', suffix='.json.tmp', delete=False) as output:
            temporary.append(Path(output.name))
            output.write(json.dumps(identity, sort_keys=True) + '\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary[0], archive)
        os.replace(temporary[1], manifest)
        return identity
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def _manifest(path: Path) -> dict:
    try:
        with path.open('rb') as incoming:
            raw = incoming.read(4097)
        identity = json.loads(raw) if len(raw) <= 4096 else None
    except (OSError, ValueError, UnicodeError) as exc:
        raise RuntimeError('Could not read the bundled snapshot manifest') from exc
    if (not isinstance(identity, dict) or set(identity) != {'version', 'bytes', 'sha256'}
            or type(identity['version']) is not int or identity['version'] != 1
            or type(identity['bytes']) is not int or identity['bytes'] <= 0
            or not isinstance(identity['sha256'], str)
            or re.fullmatch(r'[0-9a-f]{64}', identity['sha256']) is None):
        raise RuntimeError('Invalid bundled snapshot manifest')
    return identity


def _matches(path: Path, identity: dict) -> bool:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != identity['bytes']:
            return False
        digest = hashlib.sha256()
        with path.open('rb') as incoming:
            while block := incoming.read(CHUNK_SIZE):
                digest.update(block)
        return digest.hexdigest() == identity['sha256']
    except OSError:
        return False


def _extract_snapshot(archive: Path, destination: Path, identity: dict) -> Path:
    temporary = None
    try:
        digest, size = hashlib.sha256(), 0
        with tempfile.NamedTemporaryFile(
                dir=destination.parent, prefix=f".snapshot-{identity['sha256']}-",
                suffix='.db.tmp', delete=False) as outgoing:
            temporary = Path(outgoing.name)
            with gzip.open(archive, 'rb') as incoming:
                while block := incoming.read(CHUNK_SIZE):
                    size += len(block)
                    if size > identity['bytes']:
                        raise RuntimeError('Bundled snapshot exceeds its declared byte count')
                    digest.update(block)
                    outgoing.write(block)
            if size != identity['bytes'] or digest.hexdigest() != identity['sha256']:
                raise RuntimeError('Bundled snapshot byte count or SHA256 does not match')
            outgoing.flush()
            os.fsync(outgoing.fileno())
        temporary.chmod(0o444)
        os.replace(temporary, destination)
        return destination
    except (OSError, EOFError, zlib.error) as exc:
        raise RuntimeError('Could not materialize the compressed deal snapshot') from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_snapshot_bundle(archive: Path, manifest: Path, *, cache_dir: Path | None = None) -> Path:
    """Verify cached bytes, or serialize one atomic extraction per snapshot digest."""
    # The deployment and development hosts are POSIX. Keep this import on the
    # compressed path so ordinary uncompressed local usage needs no OS lock.
    import fcntl

    identity = _manifest(manifest)
    if not archive.is_file() or archive.stat().st_size == 0:
        raise RuntimeError('Compressed deal snapshot is missing or empty')
    cache_dir = cache_dir or Path(tempfile.gettempdir()) / 'freshpowder-snapshots'
    cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = cache_dir / f"deals-{identity['sha256']}.db"
    if _matches(destination, identity):
        return destination
    lock_path = cache_dir / f".{identity['sha256']}.lock"
    with lock_path.open('a+b') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            # Another initializer may have finished while this process waited.
            if _matches(destination, identity):
                return destination
            # A killed initializer cannot run its finally block. The digest
            # lock proves none of these task-owned partial files is active.
            for abandoned in cache_dir.glob(f".snapshot-{identity['sha256']}-*.db.tmp"):
                abandoned.unlink(missing_ok=True)
            return _extract_snapshot(archive, destination, identity)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def configure_runtime_snapshot(root: Path) -> Path:
    """Set the materialized path before any database default arguments are bound."""
    if 'DATABASE_PATH' in os.environ:
        return Path(os.environ['DATABASE_PATH'])
    source = root / 'catalogs' / 'fresh-powder' / 'data' / 'deals.db'
    if not os.environ.get('VERCEL') and source.is_file():
        return source
    archive = source.with_name(source.name + '.gz')
    manifest = source.with_name(source.name + '.manifest.json')
    if os.environ.get('VERCEL') or archive.exists() or manifest.exists():
        destination = materialize_snapshot_bundle(archive, manifest)
        os.environ['DATABASE_PATH'] = str(destination)
        os.environ['DEALS_DB_READ_ONLY'] = '1'
        return destination
    return source
