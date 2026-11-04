"""Restore an explicit public catalog snapshot; never silently discard its history."""
import argparse
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "common"))
from deal_common.catalog.storage import read_sources

RELEASE_API = "https://api.github.com/repos/lifan-builds/snow-deal-data/releases/tags/latest-data"
MAX_BYTES = 100 * 1024 * 1024


def restore(catalog: str, destination: Path, *, bootstrap=False, transport=None,
            github_token: str | None = None) -> str:
    if destination.exists():
        raise ValueError("Refusing to overwrite an existing snapshot")
    with httpx.Client(timeout=60, follow_redirects=True, transport=transport) as client:
        # Authenticate only this fixed metadata endpoint, never the asset/CDN request.
        headers = {"Authorization": f"Bearer {github_token}"} if github_token else {}
        response = client.get(RELEASE_API, headers=headers, follow_redirects=False)
        response.raise_for_status()
        assets = response.json().get("assets")
        if not isinstance(assets, list):
            raise ValueError("Malformed release metadata")  # noqa: TRY004 - invalid remote response, not caller type
        asset = next((a for a in assets if a.get("name") == f"{catalog}.db"), None)
        if asset is None:
            if bootstrap:
                return "explicit-bootstrap"
            raise ValueError("Previous snapshot missing; explicit first-run bootstrap required")
        # Construct the known repository destination, never follow a metadata-supplied URL.
        url = f"https://github.com/lifan-builds/snow-deal-data/releases/download/latest-data/{catalog}.db"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
            candidate = Path(temp) / "snapshot.db"
            total = 0
            with client.stream("GET", url) as response, candidate.open("wb") as output:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("Snapshot exceeds download budget")
                    output.write(chunk)
            with sqlite3.connect(candidate.resolve().as_uri() + "?mode=ro", uri=True) as db:
                if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ValueError("Snapshot failed integrity check")
            if not read_sources(candidate, catalog):
                raise ValueError("Previous snapshot contains no source history")
            candidate.replace(destination)
    return "restored"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", choices=("cycling", "tools"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    print(restore(args.catalog, args.database, bootstrap=args.bootstrap,
                  github_token=os.environ.get("GITHUB_TOKEN")))


if __name__ == "__main__":
    main()
