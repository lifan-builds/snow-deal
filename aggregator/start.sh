#!/usr/bin/env bash
# Startup script for Render: downloads latest deals.db then starts uvicorn.
set -e

DB_DIR="$(dirname "$DATABASE_PATH")"
mkdir -p "$DB_DIR"

echo "Downloading latest deals.db from GitHub Releases..."

# Try downloading from the latest-data release
DOWNLOAD_URL="https://github.com/fantasy-cc/snow-deal/releases/download/latest-data/deals.db"

if [ -n "$GITHUB_TOKEN" ]; then
    # Private repo: use API with auth
    ASSET_URL=$(curl -sL \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/fantasy-cc/snow-deal/releases/tags/latest-data" \
        | python3 -c "import sys,json; assets=json.load(sys.stdin).get('assets',[]); print(assets[0]['url'] if assets else '')")

    if [ -n "$ASSET_URL" ]; then
        curl -sL \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/octet-stream" \
            "$ASSET_URL" \
            -o "$DATABASE_PATH"
        echo "Downloaded deals.db (private repo, $(wc -c < "$DATABASE_PATH") bytes)"
    else
        echo "WARNING: No release asset found. Starting with empty database."
    fi
else
    # Public repo: direct download
    if curl -sfL "$DOWNLOAD_URL" -o "$DATABASE_PATH"; then
        echo "Downloaded deals.db ($(wc -c < "$DATABASE_PATH") bytes)"
    else
        echo "WARNING: Could not download deals.db. Starting with empty database."
    fi
fi

echo "Starting uvicorn..."
exec uvicorn aggregator.web.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
