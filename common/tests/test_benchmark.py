from copy import deepcopy

from deal_common.benchmark import METRICS, compare, evaluate


def observation(value):
    return dict(status="measured", value=value, evidence="sample.csv", sample_size=30,
                cohort="US-new-tools-200", method="audit-v1", date="2026-11-02", environment="production")


def test_unknown_claims_and_missing_evidence_cannot_be_wins():
    for bad in ({}, {**observation(0), "status": "claimed"}, {**observation(0), "evidence": ""},
                {**observation(0), "sample_size": 0}, observation(float("nan")), observation(-1)):
        assert compare("M2", observation(5), bad, as_of="2026-11-02") == "unproven"


def test_cohorts_dates_and_local_speed_cannot_be_compared():
    for field in ("cohort", "method", "date"):
        bad = {**observation(1000), field: "2026-11-01" if field == "date" else "different"}
        assert compare("M10", observation(500), bad, as_of="2026-11-02") == "incomparable"
    assert compare("M10", {**observation(10), "environment": "local"}, observation(500), as_of="2026-11-02") == "incomparable"
    assert compare("M2", observation(5), observation(1), as_of="2026-12-02") == "unproven"


def test_ceilings_targets_margins_and_confidence():
    assert len(METRICS) == 10
    assert compare("M6", observation(100), observation(100), as_of="2026-11-02") == "parity"
    assert compare("M7", observation(94), observation(80), as_of="2026-11-02") == "below-target"
    assert compare("M1", observation(110), observation(100), as_of="2026-11-02") == "below-margin"
    assert compare("M1", observation(120), observation(100), as_of="2026-11-02") == "lead"
    assert compare("M3", observation(100), observation(90), as_of="2026-11-02") == "unproven"
    assert compare("M3", {**observation(100), "interval": [88, 100]},
                   {**observation(90), "interval": [75, 98]}, as_of="2026-11-02") == "unproven"


def test_every_metric_and_relevant_rival_is_required():
    report = {"date": "2026-11-02", "sites": [
        {"name": "Us", "ours": True, "categories": ["tools"], "metrics": {}},
        {"name": "Rival", "categories": ["tools"], "metrics": {"M2": observation(2)}},
        {"name": "Snow", "categories": ["snow"], "metrics": {}}]}
    rows = evaluate(deepcopy(report))
    assert len(rows) == 10 and all(row["result"] == "unproven" for row in rows)


def test_fast_lcp_cannot_hide_layout_shift_or_one_run():
    own = {**observation(1000), "cls": 0.05, "sample_size": 3}
    rival = {**observation(2000), "cls": 0.05, "sample_size": 3}
    assert compare("M10", own, rival, as_of="2026-11-02") == "lead"
    assert compare("M10", {**own, "cls": 0.2}, rival, as_of="2026-11-02") == "below-target"
    assert compare("M10", {**own, "sample_size": 1}, rival, as_of="2026-11-02") == "unproven"
    assert compare("M10", own, observation(2000), as_of="2026-11-02") == "unproven"
