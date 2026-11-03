"""Render a dated competitive matrix; --require-lead rejects unsupported win claims."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "common"))
from deal_common.benchmark import evaluate, markdown  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-lead", action="store_true")
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    print(markdown(report))
    results = evaluate(report)
    return int(args.require_lead and (not results or any(row["result"] != "lead" for row in results)))


if __name__ == "__main__":
    raise SystemExit(main())
