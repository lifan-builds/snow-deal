"""Public snapshot identity for proving that a deployment contains fresh data."""
import hashlib
import json
from datetime import UTC, datetime

from deal_common.catalog.query import is_fresh


def snapshot_health(catalog, rows, *, now=None):
    now = now or datetime.now(UTC)
    configured = {source.name for source in catalog.sources}
    selected = sorted((row for row in rows if row["name"] in configured), key=lambda row: row["name"])
    payload = [{"source": row["name"], "observed_at": row["successful_at"],
                "products": row["products"]} for row in selected]
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False,
                                            separators=(",", ":")).encode()).hexdigest()
    complete = sum(row["status"] == "complete" and is_fresh(row["successful_at"], now) for row in selected)
    return {"catalog": catalog.slug, "snapshot_sha256": fingerprint,
            "fresh_sources": complete, "configured_sources": len(configured),
            "status": "ready" if complete == len(configured) else "degraded"}
