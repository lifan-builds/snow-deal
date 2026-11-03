"""Build a separate Vercel project from explicit, fresh catalog data. Never deploys."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
for source in ("common", "catalogs/cycling/src", "catalogs/tools/src"):
    sys.path.insert(0, str(ROOT / source))

from deal_common.catalog.health import snapshot_health
from deal_common.catalog.query import is_fresh, query
from deal_common.catalog.storage import database as open_database
from deal_common.catalog.storage import read_sources, save_source


def package(slug: str, database: Path, output: Path, public_url: str | None = None) -> dict:
    if slug == "cycling":
        from cycling_deals.catalog import CATALOG
        module = "cycling_deals"
    elif slug == "tools":
        from tool_deals.catalog import CATALOG
        module = "tool_deals"
    else:
        raise ValueError("Choose cycling or tools")
    if public_url:
        parsed = urlsplit(public_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
            raise ValueError("Public URL must be an HTTPS origin")
        public_url = public_url.rstrip("/")
    if output.exists():
        raise ValueError("Output already exists; choose a new build directory")
    rows = {row["name"]: row for row in read_sources(database, slug)}
    now = datetime.now(UTC)
    selected = []
    for source in CATALOG.sources:
        row = rows.get(source.name)
        if not row or row["status"] != "complete" or not is_fresh(row["successful_at"], now):
            raise ValueError(f"A fresh, complete snapshot is required for {source.name}")
        selected.append(row)
    results = query(selected, {"min_reference": CATALOG.default_reference, "max_price": 0,
                                   "min_discount": 0, "page": 1}, now=now)
    if results["total"] == 0:
        raise ValueError("Refusing to package an empty default catalog")
    output.mkdir(parents=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(ROOT / "common/deal_common", output / "src/deal_common", ignore=ignore)
    shutil.copytree(ROOT / f"catalogs/{slug}/src/{module}", output / f"src/{module}", ignore=ignore)
    for row in selected:
        save_source(output / "data/catalog.db", slug, row["name"], row["successful_at"],
                    row["products"], "complete", row["detail"])
    # Preserve real observations across releases; never reset history to the
    # latest snapshot, and never copy unrelated source/operational tables.
    with open_database(database, slug) as original, open_database(output / "data/catalog.db", slug, writable=True) as bundled, bundled:
        for source in CATALOG.sources:
            history = original.execute(
                "SELECT source, observed_at, products FROM observations WHERE source=? AND observed_at>=? AND observed_at<=?",
                (source.name, (now - timedelta(days=45)).isoformat(), now.isoformat()))
            bundled.executemany("INSERT OR REPLACE INTO observations VALUES (?, ?, ?)", history)
    api = output / "api"
    api.mkdir()
    (api / "index.py").write_text(
        "from pathlib import Path\nimport sys\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "sys.path.insert(0, str(ROOT / 'src'))\n"
        f"from {module}.catalog import CATALOG\n"
        "from deal_common.catalog.web import create_app\n"
        f"app = create_app(CATALOG, ROOT / 'data/catalog.db', public_url={public_url!r})\n"
    )
    dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    (output / "requirements.txt").write_text("\n".join(dependencies) + "\n")
    (output / "vercel.json").write_text(json.dumps({
        "version": 2,
        "functions": {"api/index.py": {"includeFiles": "{src/**,data/catalog.db}"}},
        "rewrites": [{"source": "/(.*)", "destination": "/api/index.py"}],
    }, indent=2) + "\n")
    receipt = {"catalog": slug, "brand": CATALOG.name, "built_at": now.isoformat(),
                   "snapshot_sha256": snapshot_health(CATALOG, selected, now=now)["snapshot_sha256"],
                   "public_url": public_url, "matching_deals": results["total"],
                   "sources": [{"name": row["name"], "observed_at": row["successful_at"],
                                 "listings": len(row["products"])} for row in selected]}
    (output / "BUILD-RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", choices=("cycling", "tools"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--public-url")
    args = parser.parse_args()
    print(json.dumps(package(args.catalog, args.database, args.output, args.public_url), indent=2))


if __name__ == "__main__":
    main()
