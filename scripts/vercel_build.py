"""Prepare FreshPowder assets for Vercel.

Vercel's Python functions should not download or mutate the deal database at
request time. This build step fetches the latest public SQLite snapshot and
copies static assets into public/ so Vercel can serve them directly.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalogs" / "fresh-powder"
STATIC_SRC = CATALOG / "src" / "aggregator" / "web" / "static"
STATIC_DEST = ROOT / "public" / "static"
DB_DEST = CATALOG / "data" / "deals.db"
DEFAULT_DB_URL = (
    "https://github.com/lifan-builds/snow-deal-data/"
    "releases/download/latest-data/deals.db"
)


def log(message: str) -> None:
    print(f"[vercel_build] {message}", flush=True)


def copy_static_assets() -> None:
    if STATIC_DEST.exists():
        shutil.rmtree(STATIC_DEST)
    shutil.copytree(STATIC_SRC, STATIC_DEST)
    log(f"Copied static assets to {STATIC_DEST.relative_to(ROOT)}")


def validate_sqlite_db(db_path: Path) -> tuple[int, str | None]:
    if not db_path.exists() or db_path.stat().st_size == 0:
        raise RuntimeError(f"{db_path} does not exist or is empty")

    conn = sqlite3.connect(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or str(integrity[0]).lower() != "ok":
            raise RuntimeError(f"integrity_check returned {integrity!r}")
        count, latest = conn.execute(
            "SELECT COUNT(*), MAX(scraped_at) FROM deals"
        ).fetchone()
    finally:
        conn.close()

    return int(count), latest


def _drop_redundant_history_index(conn: sqlite3.Connection) -> bool:
    indexes = conn.execute('PRAGMA index_list("price_history")').fetchall()
    target = next((row for row in indexes if row[1] == "idx_history_url"), None)
    if target is None or target[2:] != (0, "c", 0):
        return False

    def key_columns(name):
        return conn.execute(
            'SELECT cid, name, "desc", coll FROM pragma_index_xinfo(?) '
            'WHERE "key"=1 ORDER BY seqno', (name,)
        ).fetchall()

    keys = key_columns(target[1])
    if not keys or any(column[0] < 0 for column in keys):
        return False
    if not any(row[2:] == (1, "pk", 0) and key_columns(row[1]) == keys for row in indexes):
        return False
    conn.execute('DROP INDEX "idx_history_url"')
    return True


def compact_downloaded_db(db_path: Path) -> tuple[int, str | None]:
    """Repack the temporary build snapshot without removing observations."""
    before = validate_sqlite_db(db_path)
    if before[0] == 0:
        raise RuntimeError("Refusing to deploy an empty deal snapshot")
    original_bytes = db_path.stat().st_size
    conn = sqlite3.connect(db_path)
    try:
        # Historical snapshots may contain the same B-tree twice. Keep the
        # primary-key index and retain any unexpected named-index definition.
        if _drop_redundant_history_index(conn):
            log("Removed duplicate history index from downloaded DB; primary key retained")
        conn.execute("VACUUM")
    finally:
        conn.close()
    after = validate_sqlite_db(db_path)
    if after != before:
        raise RuntimeError("Snapshot count or freshness changed during compaction")
    log(f"Compacted downloaded DB from {original_bytes} to {db_path.stat().st_size} bytes")
    return after


def download_deals_db() -> None:
    if os.environ.get("VERCEL_SKIP_DB_DOWNLOAD", "").lower() in {"1", "true", "yes"}:
        count, latest = validate_sqlite_db(DB_DEST)
        log(f"Skipped DB download; using existing DB with {count} deals, latest={latest}")
        return

    url = os.environ.get("DEALS_DB_DOWNLOAD_URL", DEFAULT_DB_URL)
    DB_DEST.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="deals.", suffix=".db", dir=DB_DEST.parent, delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        log(f"Downloading latest deals DB from {url}")
        with urlopen(url, timeout=60) as response, tmp_path.open("wb") as out:
            shutil.copyfileobj(response, out)
        # Migrate only the downloaded deal snapshot, never auth data.
        sys.path.insert(0, str(ROOT / "common"))
        sys.path.insert(0, str(ROOT / "catalogs/fresh-powder/src"))
        import asyncio

        from aggregator.db import init_db, repair_deal_categories
        from aggregator.reviews import compute_and_store_deal_reviews
        asyncio.run(init_db(tmp_path))
        corrected = asyncio.run(repair_deal_categories(tmp_path))
        log(f"Corrected {corrected} catalog categories without changing price timestamps")
        # Reconcile old snapshots with the current model-matching rules.
        matches = asyncio.run(compute_and_store_deal_reviews(tmp_path))
        log(f"Verified {matches} model review matches")
        # Repeated refreshes can leave partly filled pages even with a zero
        # freelist. Compact only this downloaded copy, after build migrations.
        count, latest = compact_downloaded_db(tmp_path)
        tmp_path.replace(DB_DEST)
        log(f"Prepared deals DB with {count} deals, latest={latest}")
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def main() -> int:
    try:
        copy_static_assets()
        download_deals_db()
    except Exception as exc:
        print(f"[vercel_build] ERROR: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
