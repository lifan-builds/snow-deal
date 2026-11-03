"""Evidence-aware competitive comparisons; unknown measurements never become wins."""
from datetime import date
from math import isfinite

METRICS = {
    "M1": ("Deep-deal coverage", "higher", 0),
    "M2": ("Useful retailers", "higher", 0),
    "M3": ("Price accuracy %", "higher", 99),
    "M4": ("Fit/stock accuracy %", "higher", 99),
    "M5": ("Category precision %", "higher", 99),
    "M6": ("Reference evidence %", "higher", 100),
    "M7": ("Checked within 24h %", "higher", 95),
    "M8": ("30-day history coverage %", "higher", 90),
    "M9": ("Initial mobile scroll px", "lower", 0),
    "M10": ("Mobile median LCP ms", "lower", 2500),
}


def compare(metric: str, own: dict, rival: dict, *, as_of: str) -> str:
    """Strictly compare a dated pair, without confusing a ceiling tie with a win."""
    _, direction, target = METRICS[metric]
    for observation in (own, rival):
        value = observation.get("value")
        if (observation.get("status") != "measured" or isinstance(value, bool)
                or not isinstance(value, (int, float)) or not isfinite(value) or value < 0
                or not observation.get("evidence") or not observation.get("sample_size", 0)):
            return "unproven"
        if metric in {"M3", "M4", "M5", "M6", "M7", "M8"} and value > 100:
            return "unproven"
        try:
            if not 0 <= (date.fromisoformat(as_of) - date.fromisoformat(observation["date"])).days <= 7:
                return "unproven"
        except (KeyError, TypeError, ValueError):
            return "unproven"
    for field in ("cohort", "method", "date"):
        if not own.get(field) or own[field] != rival.get(field):
            return "incomparable"
    if metric == "M10" and (own.get("environment") != "production" or rival.get("environment") != "production"):
        return "incomparable"
    if metric == "M10":
        for observation in (own, rival):
            cls = observation.get("cls")
            if (observation["sample_size"] < 3 or isinstance(cls, bool)
                    or not isinstance(cls, (int, float)) or not isfinite(cls) or cls < 0):
                return "unproven"
        if own["cls"] > 0.1:
            return "below-target"
    if metric in {"M3", "M4", "M5"}:
        # A point estimate cannot establish superiority for sampled accuracy.
        if any(not isinstance(o.get("interval"), list) or len(o["interval"]) != 2
               or not 0 <= o["interval"][0] <= o["value"] <= o["interval"][1] <= 100
               for o in (own, rival)):
            return "unproven"
    a, b = own["value"], rival["value"]
    if (direction == "higher" and a < target) or (direction == "lower" and a > target):
        return "below-target"
    if a == b:
        return "parity"
    if metric in {"M3", "M4", "M5"} and own["interval"][0] <= rival["interval"][1]:
        return "unproven" if a > b else "behind"
    if metric == "M1" and b > 0 and b < a < b * 1.2:
        return "below-margin"
    return "lead" if (a > b if direction == "higher" else a < b) else "behind"


def evaluate(report: dict) -> list[dict]:
    rows = []
    for own in report["sites"]:
        if not own.get("ours"):
            continue
        for rival in report["sites"]:
            if rival.get("ours") or not set(own["categories"]) & set(rival["categories"]):
                continue
            # Capability comparators stay in the matrix, but cannot establish a US lead.
            for metric in METRICS:
                result = compare(metric, own.get("metrics", {}).get(metric, {}),
                                 rival.get("metrics", {}).get(metric, {}), as_of=report["date"])
                rows.append({"site": own["name"], "rival": rival["name"], "metric": metric, "result": result})
    return rows


def markdown(report: dict) -> str:
    lines = [f"# Competitive measurements — {report['date']}", "",
             "U = unmeasured; C = provider claim; O = observed surface, not a validated metric.",
             "Numbers are meaningful only with the cohort/method/evidence in the JSON. See COMPETITIVE-BENCHMARK.md.", "",
             "| Site | " + " | ".join(METRICS) + " |", "|---|" + "---|" * len(METRICS)]
    for site in report["sites"]:
        cells = []
        for metric in METRICS:
            item = site.get("metrics", {}).get(metric, {})
            status = item.get("status", "unknown")
            cells.append(str(item["value"]) if status == "measured" else {"claimed": "C", "observed": "O"}.get(status, "U"))
        lines.append("| " + site["name"] + " | " + " | ".join(cells) + " |")
    results = evaluate(report)
    lines += ["", f"Verified strict leads: {sum(r['result'] == 'lead' for r in results)} / {len(results)} comparisons.",
              "Parity is not a strict win. Unmeasured or incomparable evidence blocks an all-metrics lead claim.", ""]
    return "\n".join(lines)
