"""Auth database — invite codes, sessions, events.

Uses Turso (cloud SQLite via libsql embedded replica) when TURSO_URL is
set, otherwise falls back to a local SQLite file (auth.db) for development.

The libsql package provides a sqlite3-compatible sync API with a local
replica that syncs to Turso cloud. Reads are instant (local), writes
are pushed via .sync().
"""

from __future__ import annotations

import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")

AUTH_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS invite_codes (
        code       TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        max_uses   INTEGER NOT NULL DEFAULT 5
    )""",
    """CREATE TABLE IF NOT EXISTS sessions (
        token       TEXT PRIMARY KEY,
        invite_code TEXT NOT NULL,
        created_at  TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS events (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT    NOT NULL,
        session    TEXT,
        deal_url   TEXT,
        deal_name  TEXT,
        store      TEXT,
        category   TEXT,
        metadata   TEXT,
        created_at TEXT    NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS waitlist (
        email      TEXT PRIMARY KEY,
        created_at TEXT NOT NULL
    )""",
]

# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_conn = None


def _get_conn():
    """Return a reusable database connection (created on first call)."""
    global _conn
    if _conn is not None:
        return _conn

    if TURSO_URL:
        import libsql
        local_path = os.environ.get("AUTH_DB_PATH", "auth_replica.db")
        _conn = libsql.connect(
            local_path,
            sync_url=TURSO_URL,
            auth_token=TURSO_AUTH_TOKEN,
        )
        _conn.sync()
        log.info("Auth DB connected (Turso: %s)", TURSO_URL)
    else:
        db_path = Path(os.environ.get(
            "AUTH_DB_PATH",
            Path(__file__).resolve().parent.parent / "auth.db",
        ))
        _conn = sqlite3.connect(str(db_path))
        log.info("Auth DB connected (local: %s)", db_path)

    return _conn


def _sync():
    """Push local changes to Turso (no-op for local SQLite)."""
    if TURSO_URL and _conn is not None:
        _conn.sync()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

async def init_auth_db() -> None:
    """Create auth tables if they don't exist."""
    conn = _get_conn()
    for stmt in AUTH_SCHEMA:
        conn.execute(stmt)
    conn.commit()
    _sync()


# ---------------------------------------------------------------------------
# Invite codes
# ---------------------------------------------------------------------------

async def create_invite_codes(codes: list[str], max_uses: int = 5) -> int:
    """Insert invite codes. Returns count created."""
    now = datetime.now().isoformat()
    conn = _get_conn()
    created = 0
    for code in codes:
        try:
            conn.execute(
                "INSERT INTO invite_codes (code, created_at, max_uses) VALUES (?, ?, ?)",
                (code, now, max_uses),
            )
            created += 1
        except (sqlite3.IntegrityError, Exception) as e:
            if "UNIQUE" in str(e) or "IntegrityError" in type(e).__name__:
                continue
            raise
    conn.commit()
    _sync()
    return created


async def validate_invite_code(code: str) -> bool:
    """Check if an invite code is valid and under its max_uses limit."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT max_uses FROM invite_codes WHERE code = ?", (code,)
    ).fetchone()
    if not row:
        return False
    max_uses = row[0]
    use_count = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE invite_code = ?", (code,)
    ).fetchone()[0]
    return use_count < max_uses


async def record_code_use(code: str) -> None:
    """Record that an invite code was used (insert a session row for counting)."""
    now = datetime.now().isoformat()
    token = secrets.token_urlsafe(16)
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (token, invite_code, created_at) VALUES (?, ?, ?)",
        (token, code, now),
    )
    conn.commit()
    _sync()


async def list_invite_codes() -> list[dict]:
    """Return all invite codes with usage counts."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT ic.code, ic.created_at, ic.max_uses, COUNT(s.token) AS use_count "
        "FROM invite_codes ic "
        "LEFT JOIN sessions s ON s.invite_code = ic.code "
        "GROUP BY ic.code "
        "ORDER BY ic.created_at"
    ).fetchall()
    return [
        {"code": r[0], "created_at": r[1], "max_uses": r[2], "use_count": r[3]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Events / analytics
# ---------------------------------------------------------------------------

async def log_event(
    event_type: str,
    session: str | None = None,
    deal_url: str | None = None,
    deal_name: str | None = None,
    store: str | None = None,
    category: str | None = None,
    metadata: str | None = None,
) -> None:
    """Log a user event (page view, click, filter, etc.)."""
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO events (event_type, session, deal_url, deal_name, store, category, metadata, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (event_type, session, deal_url, deal_name, store, category, metadata, now),
    )
    conn.commit()
    _sync()


async def get_click_stats(days: int = 7) -> dict:
    """Get click-through statistics for the admin dashboard."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = _get_conn()

    by_type = [
        {"event_type": r[0], "cnt": r[1]}
        for r in conn.execute(
            "SELECT event_type, COUNT(*) AS cnt FROM events "
            "WHERE created_at >= ? GROUP BY event_type ORDER BY cnt DESC",
            (cutoff,),
        ).fetchall()
    ]

    clicks_by_store = [
        {"store": r[0], "cnt": r[1]}
        for r in conn.execute(
            "SELECT store, COUNT(*) AS cnt FROM events "
            "WHERE event_type = 'click' AND created_at >= ? AND store IS NOT NULL "
            "GROUP BY store ORDER BY cnt DESC",
            (cutoff,),
        ).fetchall()
    ]

    top_deals = [
        {"deal_name": r[0], "store": r[1], "deal_url": r[2], "cnt": r[3]}
        for r in conn.execute(
            "SELECT deal_name, store, deal_url, COUNT(*) AS cnt FROM events "
            "WHERE event_type = 'click' AND created_at >= ? AND deal_name IS NOT NULL "
            "GROUP BY deal_url ORDER BY cnt DESC LIMIT 20",
            (cutoff,),
        ).fetchall()
    ]

    clicks_by_day = [
        {"day": r[0], "cnt": r[1]}
        for r in conn.execute(
            "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
            "WHERE event_type = 'click' AND created_at >= ? "
            "GROUP BY day ORDER BY day",
            (cutoff,),
        ).fetchall()
    ]

    views_by_day = [
        {"day": r[0], "cnt": r[1]}
        for r in conn.execute(
            "SELECT DATE(created_at) AS day, COUNT(*) AS cnt FROM events "
            "WHERE event_type = 'page_view' AND created_at >= ? "
            "GROUP BY day ORDER BY day",
            (cutoff,),
        ).fetchall()
    ]

    row = conn.execute(
        "SELECT COUNT(DISTINCT session) AS cnt FROM events "
        "WHERE created_at >= ? AND session IS NOT NULL",
        (cutoff,),
    ).fetchone()
    unique_sessions = row[0] if row else 0

    filter_usage = [
        {"metadata": r[0], "cnt": r[1]}
        for r in conn.execute(
            "SELECT metadata, COUNT(*) AS cnt FROM events "
            "WHERE event_type = 'filter' AND created_at >= ? AND metadata IS NOT NULL "
            "GROUP BY metadata ORDER BY cnt DESC LIMIT 15",
            (cutoff,),
        ).fetchall()
    ]

    return {
        "by_type": by_type,
        "clicks_by_store": clicks_by_store,
        "top_deals": top_deals,
        "clicks_by_day": clicks_by_day,
        "views_by_day": views_by_day,
        "unique_sessions": unique_sessions,
        "filter_usage": filter_usage,
        "days": days,
    }


# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------

async def add_to_waitlist(email: str) -> bool:
    """Add an email to the waitlist. Returns True if added, False if already present."""
    now = datetime.now().isoformat()
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT INTO waitlist (email, created_at) VALUES (?, ?)",
            (email.strip().lower(), now),
        )
        conn.commit()
        _sync()
        return True
    except (sqlite3.IntegrityError, Exception) as e:
        if "UNIQUE" in str(e) or "IntegrityError" in type(e).__name__:
            return False
        raise


async def list_waitlist() -> list[dict]:
    """Return all waitlist emails."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT email, created_at FROM waitlist ORDER BY created_at DESC"
    ).fetchall()
    return [{"email": r[0], "created_at": r[1]} for r in rows]
