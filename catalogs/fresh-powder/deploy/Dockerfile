FROM python:3.12-slim

WORKDIR /app

# Install curl for downloading deals.db at startup
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install the workspace with its common and Fresh Powder packages.
COPY pyproject.toml README.md ./
COPY common/deal_common/ common/deal_common/
COPY catalogs/fresh-powder/src/ catalogs/fresh-powder/src/
RUN pip install --no-cache-dir -e .

# Default database path inside container
ENV DATABASE_PATH=/app/data/deals.db

COPY catalogs/fresh-powder/deploy/start.sh /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
