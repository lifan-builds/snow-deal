from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path

import httpx
import pytest

from tool_deals.catalog import CATALOG
from deal_common.catalog.health import snapshot_health

spec = importlib.util.spec_from_file_location("verify_live", Path(__file__).resolve().parents[2] / "scripts/verify_catalog_live.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_snapshot_identity_changes_with_prices_and_health_detects_failure():
    now = datetime.now(timezone.utc)
    catalog = replace(CATALOG, sources=(CATALOG.sources[0],))
    rows = [dict(name=catalog.sources[0].name, successful_at=now.isoformat(),
                 products=[{"price": 100}], status="complete")]
    first = snapshot_health(catalog, rows, now=now)
    assert first["status"] == "ready"
    changed = deepcopy(rows)
    changed[0]["products"][0]["price"] = 101
    assert snapshot_health(catalog, changed)["snapshot_sha256"] != first["snapshot_sha256"]
    rows[0]["status"] = "incomplete"
    assert snapshot_health(catalog, rows)["status"] == "degraded"
    rows[0]["status"] = "complete"
    assert snapshot_health(catalog, rows, now=now+timedelta(days=4))["status"] == "degraded"
    assert snapshot_health(CATALOG, rows)["status"] == "degraded"


@pytest.mark.parametrize("change", [{"snapshot_sha256": "old"}, {"catalog": "cycling"},
                                   {"status": "degraded"}, {"fresh_sources": 0}])
def test_live_verification_rejects_successful_http_for_wrong_data(change):
    receipt = {"catalog": "tools", "snapshot_sha256": "expected", "sources": [{}]}
    live = {"catalog": "tools", "snapshot_sha256": "expected", "fresh_sources": 1,
            "configured_sources": 1, "status": "ready"}
    with pytest.raises(RuntimeError):
        verifier.verify("https://benchdrop.example", receipt, attempts=1,
                        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={**live, **change})))
    assert verifier.verify("https://benchdrop.example", receipt, attempts=1,
                           transport=httpx.MockTransport(lambda r: httpx.Response(200, json=live))) == live
