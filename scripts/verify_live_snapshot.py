"""Wait for production to serve the just-published snapshot; never log deploy secrets."""
import argparse
import json
import time
from datetime import datetime
from urllib.request import Request, urlopen


def verify(url: str, expected: str, timeout: int = 600) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request = Request(url, headers={"Cache-Control": "no-cache"})
            with urlopen(request, timeout=20) as response:
                result = json.load(response)
            observed = result.get("checked_at")
            if result.get("status") == "ok" and observed and datetime.fromisoformat(observed) >= datetime.fromisoformat(expected):
                print(f"Production snapshot verified: {observed}")
                return True
        except Exception:
            pass
        time.sleep(15)
    print("Production did not serve the expected snapshot before the deadline.")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--url", default="https://snow-deal.vercel.app/healthz")
    args = parser.parse_args()
    with open(args.report) as source:
        expected = json.load(source)["checked_at"]
    raise SystemExit(0 if verify(args.url, expected) else 1)
