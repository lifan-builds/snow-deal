"""Atomic, catalog-bound snapshots. Serving never creates or changes a database."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC
from pathlib import Path


@contextmanager
def database(path: Path, catalog: str, *, writable: bool = False):
    if writable:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
    else:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if writable:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS metadata (catalog TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sources (
                    name TEXT PRIMARY KEY, checked_at TEXT, successful_at TEXT,
                    status TEXT NOT NULL, detail TEXT NOT NULL,
                    products TEXT NOT NULL DEFAULT '[]'
                );
                CREATE TABLE IF NOT EXISTS observations (
                    source TEXT NOT NULL, observed_at TEXT NOT NULL,
                    products TEXT NOT NULL,
                    PRIMARY KEY (source, observed_at)
                );
            """)
        identity = connection.execute("SELECT catalog FROM metadata").fetchone()
        if identity is None and writable:
            connection.execute("INSERT INTO metadata VALUES (?)", (catalog,))
            connection.commit()
        elif identity is None or identity[0] != catalog:
            raise ValueError("Snapshot belongs to a different catalog")
        yield connection
    finally:
        connection.close()


def save_source(path: Path, catalog: str, name: str, observed_at: str,
                products: list[dict], status: str, detail: dict):
    with database(path, catalog, writable=True) as connection, connection:
        connection.execute("""
            INSERT INTO sources (name, checked_at, status, detail) VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET checked_at=excluded.checked_at,
                status=excluded.status, detail=excluded.detail
        """, (name, observed_at, status, json.dumps(detail)))
        if status == "complete":
            payload = json.dumps(products, allow_nan=False)
            connection.execute("UPDATE sources SET products=?, successful_at=? WHERE name=?",
                               (payload, observed_at, name))
            connection.execute("INSERT OR REPLACE INTO observations VALUES (?, ?, ?)",
                               (name, observed_at, payload))
            # History is daily evidence, not every retry. Keep the latest successful
            # observation per UTC day and a bounded 45-day window for release assets.
            connection.execute("""
                DELETE FROM observations WHERE source=? AND (
                    datetime(observed_at) < datetime(?, '-45 days') OR
                    (date(observed_at)=date(?) AND datetime(observed_at)<datetime(?)))
            """, (name, observed_at, observed_at, observed_at))


def read_sources(path: Path, catalog: str) -> list[dict]:
    if not path.exists():
        return []
    with database(path, catalog) as connection:
        rows = [dict(row) for row in connection.execute("SELECT * FROM sources ORDER BY name")]
    for row in rows:
        row["products"] = json.loads(row["products"])
        row["detail"] = json.loads(row["detail"])
    return rows


def read_offer_history(path: Path, catalog: str, source: str, product: dict, offer: dict,
                       *, now, days: int = 45) -> list[dict]:
    """One successful observation per UTC day, for the exact current identity only."""
    from datetime import datetime, timedelta
    cutoff = now - timedelta(days=days)
    with database(path, catalog) as connection:
        rows = connection.execute("""
            SELECT observed_at, products FROM observations
            WHERE source=? AND observed_at>=? AND observed_at<=?
            ORDER BY observed_at
        """, (source, cutoff.isoformat(), now.isoformat())).fetchall()
    daily = {}
    for row in rows:
        stamp = datetime.fromisoformat(row["observed_at"])
        if stamp.tzinfo is None or not cutoff <= stamp <= now:
            continue
        for historical in json.loads(row["products"]):
            if (historical["url"], historical["name"], historical["brand"]) != (product["url"], product["name"], product["brand"]):
                continue
            for candidate in historical["offers"]:
                if (candidate["variant_key"], candidate["options"], candidate["url"]) != (offer["variant_key"], offer["options"], offer["url"]):
                    continue
                daily[stamp.astimezone(UTC).date().isoformat()] = {
                    "observed_at": row["observed_at"], "price": candidate["current_price"],
                    "reference": candidate["original_price"], "availability": candidate["availability"],
                    "availability_note": candidate.get("availability_note", "")}
    return list(reversed(daily.values()))
