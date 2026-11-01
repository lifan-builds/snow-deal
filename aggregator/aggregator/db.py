"""SQLite schema and CRUD operations via aiosqlite."""

from __future__ import annotations

import os
import aiosqlite
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from aggregator.config import env_flag, STORES
from aggregator.models import AggregatedDeal

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).resolve().parent.parent / "deals.db"))

SCHEMA = """\
CREATE TABLE IF NOT EXISTS deals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    store         TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    url           TEXT    NOT NULL UNIQUE,
    current_price REAL    NOT NULL,
    original_price REAL,
    discount_pct  REAL    NOT NULL DEFAULT 0,
    category      TEXT,
    sizes         TEXT,
    length_min    INTEGER,
    length_max    INTEGER,
    scraped_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_discount  ON deals (discount_pct DESC);
CREATE INDEX IF NOT EXISTS idx_category  ON deals (category);
CREATE INDEX IF NOT EXISTS idx_store     ON deals (store);

CREATE TABLE IF NOT EXISTS reviews (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name  TEXT    NOT NULL,
    brand         TEXT    NOT NULL DEFAULT '',
    score         INTEGER NOT NULL,
    award         TEXT,
    review_url    TEXT    NOT NULL UNIQUE,
    category      TEXT,
    scraped_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS deal_reviews (
    deal_id     INTEGER NOT NULL,
    review_id   INTEGER NOT NULL,
    score       INTEGER NOT NULL,
    award       TEXT,
    review_url  TEXT    NOT NULL,
    PRIMARY KEY (deal_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    url TEXT NOT NULL, observed_at TEXT NOT NULL, price REAL NOT NULL,
    PRIMARY KEY (url, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_history_url ON price_history(url, observed_at);
CREATE TABLE IF NOT EXISTS scrape_runs (
    store TEXT PRIMARY KEY, checked_at TEXT NOT NULL, status TEXT NOT NULL,
    deals INTEGER NOT NULL, errors INTEGER NOT NULL, pages INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_deal_reviews_score ON deal_reviews (score DESC);

"""


MIGRATIONS = [
    "ALTER TABLE deals ADD COLUMN first_seen TEXT",
    "ALTER TABLE deals ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'",
    "ALTER TABLE deals ADD COLUMN sizes TEXT",
    "ALTER TABLE deals ADD COLUMN length_min INTEGER",
    "ALTER TABLE deals ADD COLUMN length_max INTEGER",
    "ALTER TABLE deals ADD COLUMN image_url TEXT",
    "ALTER TABLE deals ADD COLUMN brand TEXT",
    "CREATE INDEX IF NOT EXISTS idx_brand ON deals (brand)",
]


def _deal_db_read_only() -> bool:
    """Return True when deal data should be opened read-only."""
    return env_flag("DEALS_DB_READ_ONLY") or bool(os.environ.get("VERCEL"))


def _sqlite_uri(db_path: Path, mode: str) -> str:
    """Build a SQLite file URI for paths that may contain spaces."""
    path = Path(db_path).resolve().as_posix()
    return f"file:{quote(path, safe='/')}?mode={mode}"


def _connect(db_path: Path, *, read_only: bool = False):
    """Open a SQLite connection, optionally forcing read-only mode."""
    if read_only:
        return aiosqlite.connect(_sqlite_uri(db_path, "ro"), uri=True)
    return aiosqlite.connect(db_path)


async def ensure_deals_db_ready(db_path: Path = DB_PATH) -> None:
    """Validate the bundled deals database without writing to it."""
    if not db_path.exists() or db_path.stat().st_size == 0:
        raise RuntimeError(
            f"Deal database not found at {db_path}. "
            "Run scripts/vercel_build.py during deployment or set DATABASE_PATH."
        )

    async with _connect(db_path, read_only=True) as db:
        cursor = await db.execute("PRAGMA integrity_check")
        row = await cursor.fetchone()
        if not row or str(row[0]).lower() != "ok":
            raise RuntimeError(f"Deal database integrity check failed: {row!r}")

        try:
            cursor = await db.execute("SELECT COUNT(*) FROM deals")
            await cursor.fetchone()
        except Exception as exc:
            raise RuntimeError(
                f"Deal database at {db_path} is missing the deals table."
            ) from exc


async def init_db(db_path: Path = DB_PATH) -> None:
    """Create tables and apply migrations."""
    async with _connect(db_path) as db:
        await db.executescript(SCHEMA)
        for migration in MIGRATIONS:
            try:
                await db.execute(migration)
            except Exception:
                pass  # column/index already exists
        await db.execute("UPDATE deals SET first_seen = scraped_at WHERE first_seen IS NULL")
        for store in STORES:
            await db.execute("UPDATE deals SET currency = ? WHERE store = ?", (store.currency, store.name))
        await db.commit()


async def upsert_deals(deals: list[AggregatedDeal], db_path: Path = DB_PATH) -> int:
    """Insert or update deals. Returns count of rows affected."""
    async with _connect(db_path) as db:
        count = 0
        for d in deals:
            currency = next((store.currency for store in STORES if store.name == d.store), d.currency)
            prior = await (await db.execute("SELECT current_price, scraped_at FROM deals WHERE url = ?", (d.url,))).fetchone()
            if prior:
                await db.execute("INSERT OR IGNORE INTO price_history VALUES (?, ?, ?)", (d.url, prior[1], prior[0]))
            await db.execute("INSERT OR REPLACE INTO price_history VALUES (?, ?, ?)", (d.url, d.scraped_at.isoformat(), d.current_price))
            await db.execute(
                """\
                INSERT INTO deals (store, name, url, current_price, original_price,
                                   discount_pct, category, sizes, length_min, length_max,
                                   scraped_at, image_url, brand, first_seen, currency)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    store          = excluded.store,
                    name           = excluded.name,
                    current_price  = excluded.current_price,
                    original_price = excluded.original_price,
                    discount_pct   = excluded.discount_pct,
                    category       = excluded.category,
                    sizes          = excluded.sizes,
                    length_min     = excluded.length_min,
                    length_max     = excluded.length_max,
                    scraped_at     = excluded.scraped_at,
                    image_url      = excluded.image_url,
                    brand          = excluded.brand,
                    currency       = excluded.currency
                """,
                (
                    d.store, d.name, d.url, d.current_price, d.original_price,
                    d.discount_pct, d.category, d.sizes, d.length_min, d.length_max,
                    d.scraped_at.isoformat(), d.image_url, d.brand, d.scraped_at.isoformat(), currency,
                ),
            )
            count += 1
        await db.commit()
    return count


async def upsert_deal_reviews(
    rows: list[dict],
    db_path: Path = DB_PATH,
) -> int:
    """Insert or replace deal→review matches. Each row: deal_id, review_id, score, award, review_url."""
    async with _connect(db_path) as db:
        count = 0
        for r in rows:
            await db.execute(
                """\
                INSERT OR REPLACE INTO deal_reviews (deal_id, review_id, score, award, review_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (r["deal_id"], r["review_id"], r["score"], r.get("award"), r["review_url"]),
            )
            count += 1
        await db.commit()
    return count


async def count_with_length(db_path: Path = DB_PATH) -> int:
    """Return count of deals that have length data."""
    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        cursor = await db.execute(
            """SELECT COUNT(*) FROM deals d
               WHERE length_min IS NOT NULL AND category IN ('skis', 'snowboards')
               AND scraped_at = (SELECT MAX(scraped_at) FROM deals WHERE store = d.store)
               AND datetime(scraped_at) >= datetime('now', '-72 hours')"""
        )
        row = await cursor.fetchone()
    return row[0]


async def get_brands(db_path: Path = DB_PATH) -> list[str]:
    """Return distinct brand names from the brand column, sorted."""
    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        cursor = await db.execute(
            """
            SELECT DISTINCT deals.brand FROM deals
            INNER JOIN (SELECT store, MAX(scraped_at) as max_s FROM deals GROUP BY store) d2 
              ON deals.store = d2.store AND deals.scraped_at = d2.max_s
            WHERE deals.brand IS NOT NULL AND deals.brand != ''
            AND datetime(deals.scraped_at) >= datetime('now', '-72 hours')
            ORDER BY deals.brand
            """
        )
        rows = await cursor.fetchall()
    return [row[0] for row in rows if row[0]]


async def get_category_counts(db_path: Path = DB_PATH) -> dict[str, int]:
    """Return {category: deal_count} for all non-null categories."""
    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        cursor = await db.execute(
            """
            SELECT deals.category, COUNT(*) FROM deals
            INNER JOIN (SELECT store, MAX(scraped_at) as max_s FROM deals GROUP BY store) d2 
              ON deals.store = d2.store AND deals.scraped_at = d2.max_s
            WHERE deals.category IS NOT NULL
            AND datetime(deals.scraped_at) >= datetime('now', '-72 hours')
            GROUP BY deals.category
            """
        )
        rows = await cursor.fetchall()
    return {row[0]: row[1] for row in rows}


async def query_deals(
    *,
    category: str | None = None,
    store: str | None = None,
    brand: str | None = None,
    min_discount: float = 0,
    min_price: float = 0,
    max_price: float = 0,
    sort_by: str = "discount_pct",
    limit: int = 200,
    offset: int = 0,
    tax_free_only: bool = False,
    tax_free_stores: set[str] | None = None,
    q: str = "",
    size_min: int | None = None,
    size_max: int | None = None,
    reviewed_only: bool = False,
    count_only: bool = False,
    currency: str | None = None,
    db_path: Path = DB_PATH,
) -> list[AggregatedDeal] | int:
    """Query deals with optional filters. If count_only=True, returns int."""
    clauses: list[str] = [
        "deals.discount_pct >= ?",
        "deals.current_price >= 1 AND deals.discount_pct < 95",
        "datetime(deals.scraped_at) >= datetime('now', '-72 hours')",
    ]
    params: list[object] = [min_discount]

    if currency in {"USD", "CAD"}:
        clauses.append("deals.currency = ?")
        params.append(currency)
    # Never compare nominal USD and CAD prices as if they were the same currency.
    elif sort_by in {"price_low", "price_high"} or min_price > 0 or max_price > 0:
        clauses.append("deals.currency = 'USD'")

    if min_price > 0:
        clauses.append("deals.current_price >= ?")
        params.append(min_price)

    if max_price > 0:
        clauses.append("deals.current_price <= ?")
        params.append(max_price)

    if category:
        clauses.append("deals.category = ?")
        params.append(category)
    if store:
        clauses.append("deals.store = ?")
        params.append(store)
    if brand:
        clauses.append("deals.brand = ?")
        params.append(brand)
    if tax_free_only and tax_free_stores:
        placeholders = ", ".join("?" for _ in tax_free_stores)
        clauses.append(f"deals.store IN ({placeholders})")
        params.extend(tax_free_stores)
    if q:
        clauses.append("deals.name LIKE ?")
        params.append(f"%{q}%")
    if size_min is not None or size_max is not None:
        # Exclude NULL-length deals when a length filter is active
        length_conds = []
        if size_min is not None and size_max is not None:
            length_conds.append("(deals.length_max >= ? AND deals.length_min <= ?)")
            params.extend([size_min, size_max])
        elif size_min is not None:
            length_conds.append("deals.length_max >= ?")
            params.append(size_min)
        elif size_max is not None:
            length_conds.append("deals.length_min <= ?")
            params.append(size_max)
        if length_conds:
            clauses.append(f"({' OR '.join(length_conds)})")
    if reviewed_only:
        clauses.append("dr.deal_id IS NOT NULL")

    where = " AND ".join(clauses)
    
    # Hide stale deals by joining against max scraped_at per store
    latest_join = "INNER JOIN (SELECT store, MAX(scraped_at) as max_s FROM deals GROUP BY store) d2 ON deals.store = d2.store AND deals.scraped_at = d2.max_s"

    if count_only:
        async with _connect(db_path, read_only=_deal_db_read_only()) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM deals {latest_join} LEFT JOIN deal_reviews dr ON deals.id = dr.deal_id WHERE {where}",
                params,
            )
            row = await cursor.fetchone()
        return row[0]

    sort_map = {
        "discount_pct": "(deals.image_url IS NOT NULL AND deals.image_url != '') DESC, deals.discount_pct DESC",
        "top_reviewed": "dr.score DESC NULLS LAST, deals.discount_pct DESC",
        "price_low": "deals.current_price ASC",
        "price_high": "deals.current_price DESC",
        "store": "deals.store ASC, deals.discount_pct DESC",
        "newest": "deals.first_seen DESC, deals.id DESC",
    }
    order = sort_map.get(sort_by, "deals.discount_pct DESC")

    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""\
            SELECT deals.*, dr.score AS review_score, dr.award AS review_award,
                   dr.review_url AS review_url,
                   (SELECT ph.price FROM price_history ph WHERE ph.url = deals.url
                    AND ph.observed_at < deals.scraped_at ORDER BY ph.observed_at DESC LIMIT 1) AS previous_price
            FROM deals
            {latest_join}
            LEFT JOIN deal_reviews dr ON deals.id = dr.deal_id
            WHERE {where}
            ORDER BY {order}
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        )
        rows = await cursor.fetchall()

    return [
        AggregatedDeal(
            first_seen=row["first_seen"], previous_price=row["previous_price"], currency=row["currency"],
            id=row["id"],
            store=row["store"],
            name=row["name"],
            url=row["url"],
            current_price=row["current_price"],
            original_price=row["original_price"],
            discount_pct=row["discount_pct"],
            category=row["category"],
            sizes=row["sizes"],
            length_min=row["length_min"],
            length_max=row["length_max"],
            scraped_at=datetime.fromisoformat(row["scraped_at"]),
            image_url=row["image_url"],
            brand=row["brand"],
            review_score=row["review_score"],
            review_award=row["review_award"],
            review_url=row["review_url"],
        )
        for row in rows
    ]


async def upsert_reviews(reviews: list, db_path: Path = DB_PATH) -> int:
    """Insert or update reviews. Accepts dicts or ReviewData NamedTuples."""
    from datetime import datetime
    now = datetime.now().isoformat()
    async with _connect(db_path) as db:
        count = 0
        for r in reviews:
            if isinstance(r, dict):
                name, brand, score = r["product_name"], r["brand"], r["score"]
                award, url, cat = r["award"], r["review_url"], r["category"]
                scraped = r.get("scraped_at", now)
            else:
                name, brand, score = r.product_name, r.brand, r.score
                award, url, cat = r.award, r.url, r.category
                scraped = now
            await db.execute(
                """\
                INSERT INTO reviews (product_name, brand, score, award, review_url, category, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_url) DO UPDATE SET
                    product_name = excluded.product_name,
                    brand        = excluded.brand,
                    score        = excluded.score,
                    award        = excluded.award,
                    category     = excluded.category,
                    scraped_at   = excluded.scraped_at
                """,
                (name, brand, score, award, url, cat, scraped),
            )
            count += 1
        await db.commit()
    return count


async def get_all_reviews(db_path: Path = DB_PATH) -> list[dict]:
    """Return all reviews from the database."""
    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, product_name, brand, score, award, review_url, category FROM reviews ORDER BY score DESC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def store_status(db_path: Path = DB_PATH) -> list[dict]:
    """Return per-store stats: deal count, deals with discounts, last scraped time."""
    async with _connect(db_path, read_only=_deal_db_read_only()) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""\
            SELECT store,
                   COUNT(*)                          AS deal_count,
                   SUM(CASE WHEN discount_pct > 0 THEN 1 ELSE 0 END) AS discount_count,
                   MAX(scraped_at)                   AS last_scraped
            FROM deals d
            INNER JOIN (SELECT store AS latest_store, MAX(scraped_at) AS latest_time FROM deals GROUP BY store) latest
                ON d.store = latest.latest_store AND d.scraped_at = latest.latest_time
            GROUP BY store
            ORDER BY store
        """)
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def save_scrape_run(report, outcomes: dict, checked_at: str, db_path: Path = DB_PATH) -> None:
    async with _connect(db_path) as db:
        for item in report.store_summaries:
            result = outcomes.get(item.store, {})
            errors = result.get("errors", 0)
            status = "unavailable" if not item.deals else ("partial" if errors else "ok")
            await db.execute("INSERT OR REPLACE INTO scrape_runs VALUES (?, ?, ?, ?, ?, ?)",
                             (item.store, checked_at, status, item.deals, errors, result.get("pages", 0)))
        await db.commit()


async def refresh_status(db_path: Path = DB_PATH) -> list[dict]:
    async with _connect(db_path, read_only=True) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute("SELECT * FROM scrape_runs ORDER BY store")).fetchall()
        return [dict(row) for row in rows]
