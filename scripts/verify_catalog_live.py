"""Verify an explicit public site serves the packaged snapshot, without credentials."""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlsplit

import httpx


def verify(site_url, receipt, *, attempts=12, pause=time.sleep, transport=None):
    parsed = urlsplit(site_url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Site URL must be an HTTPS origin")
    with httpx.Client(timeout=20, follow_redirects=False, transport=transport) as client:
        for attempt in range(attempts):
            try:
                response = client.get(site_url.rstrip("/") + "/healthz", headers={"Cache-Control": "no-cache"})
                response.raise_for_status()
                live = response.json()
                if (live.get("catalog") == receipt["catalog"] and live.get("status") == "ready"
                        and live.get("snapshot_sha256") == receipt["snapshot_sha256"]
                        and live.get("fresh_sources") == live.get("configured_sources") == len(receipt["sources"])):
                    return live
            except (httpx.HTTPError, ValueError):
                pass
            if attempt + 1 < attempts:
                pause(10)
    raise RuntimeError("Public site did not serve the expected healthy snapshot")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--site-url", required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.site_url, json.loads(args.receipt.read_text())), indent=2))


if __name__ == "__main__":
    main()
