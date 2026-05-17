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
STATIC_SRC = ROOT / "aggregator" / "aggregator" / "web" / "static"
STATIC_DEST = ROOT / "public" / "static"
DB_DEST = ROOT / "aggregator" / "deals.db"
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
        with urlopen(url, timeout=60) as response:
            with tmp_path.open("wb") as out:
                shutil.copyfileobj(response, out)
        count, latest = validate_sqlite_db(tmp_path)
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
