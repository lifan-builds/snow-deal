FROM python:3.12-slim

WORKDIR /app

# Install curl for downloading deals.db at startup
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy root package first (aggregator depends on snow-deals)
COPY pyproject.toml README.md ./
COPY snow_deals/ snow_deals/
RUN pip install --no-cache-dir -e .

# Copy and install aggregator (skip playwright binary — not needed for web serving)
COPY aggregator/ aggregator/
RUN pip install --no-cache-dir -e aggregator/

# Default database path inside container
ENV DATABASE_PATH=/app/data/deals.db

COPY aggregator/start.sh /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
