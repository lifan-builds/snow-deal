"""Restore an explicit public catalog snapshot; never silently discard its history."""
import argparse
import hashlib
import os
import re
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
        metadata = response.json()
        if not isinstance(metadata, dict):
            raise ValueError("Malformed release metadata")  # noqa: TRY004 - invalid remote response
        assets = metadata.get("assets")
        if (not isinstance(assets, list) or any(not isinstance(a, dict)
                or not isinstance(a.get("name"), str) or not a["name"] for a in assets)):
            raise ValueError("Malformed release metadata")
        matches = [a for a in assets if a["name"] == f"{catalog}.db"]
        if not matches:
            if bootstrap:
                return "explicit-bootstrap"
            raise ValueError("Previous snapshot missing; explicit first-run bootstrap required")
        if len(matches) != 1:
            raise ValueError("Ambiguous snapshot asset metadata")
        asset = matches[0]
        expected_size, digest = asset.get("size"), asset.get("digest")
        if asset.get("state") != "uploaded":
            raise ValueError("Snapshot asset is not uploaded")
        if (not isinstance(expected_size, int) or isinstance(expected_size, bool)
                or not 0 < expected_size <= MAX_BYTES):
            raise ValueError("Invalid snapshot asset size")
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest):
            raise ValueError("Missing or unsupported snapshot SHA-256 metadata")
        expected_digest = digest.removeprefix("sha256:").lower()
        # Construct the known repository destination, never follow a metadata-supplied URL.
        url = f"https://github.com/lifan-builds/snow-deal-data/releases/download/latest-data/{catalog}.db"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
            candidate = Path(temp) / "snapshot.db"
            total = 0
            actual_digest = hashlib.sha256()
            with client.stream("GET", url) as response, candidate.open("wb") as output:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("Snapshot exceeds download budget")
                    if total > expected_size:
                        raise ValueError("Snapshot byte length does not match release asset metadata")
                    actual_digest.update(chunk)
                    output.write(chunk)
            if total != expected_size:
                raise ValueError("Snapshot byte length does not match release asset metadata")
            if actual_digest.hexdigest() != expected_digest:
                raise ValueError("Snapshot SHA-256 does not match release asset metadata")
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
