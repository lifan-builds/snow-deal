"""Vercel FastAPI entrypoint for FreshPowder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for path in (ROOT / "common", ROOT / "catalogs" / "fresh-powder" / "src"):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from aggregator.bundled_snapshot import configure_runtime_snapshot

configure_runtime_snapshot(ROOT)

from aggregator.web.app import create_app

app = create_app()
