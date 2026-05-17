"""Vercel ASGI entrypoint for FreshPowder."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "aggregator"):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from aggregator.web.app import create_app

app = create_app()
