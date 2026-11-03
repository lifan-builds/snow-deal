"""Run offline tests with temporary data paths and no inherited service secrets."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="deal-aggregator-check-") as tmp:
        env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "LANG") if key in os.environ}
        env.update(
            HOME=tmp,
            PYTHONPATH=os.pathsep.join(str(ROOT / path) for path in (
                "common", "catalogs/fresh-powder/src", "catalogs/cycling/src", "catalogs/tools/src")),
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            DATABASE_PATH=str(Path(tmp) / "deals.db"),
            AUTH_DB_PATH=str(Path(tmp) / "auth.db"),
            SECRET_KEY="offline-only-test-signing-key-at-least-32-characters",
            PUBLIC_MODE="0",
        )
        return subprocess.call(
            [sys.executable, "-m", "pytest", *sys.argv[1:]], cwd=ROOT, env=env,
        )


if __name__ == "__main__":
    raise SystemExit(main())
