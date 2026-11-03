import asyncio
import json
from pathlib import Path

import click
import uvicorn

from deal_common.catalog.definition import Catalog
from deal_common.catalog.refresh import refresh
from deal_common.catalog.web import create_app


def catalog_cli(catalog: Catalog):
    @click.group()
    def cli():
        """Refresh a catalog snapshot or serve its storefront."""

    @cli.command("refresh")
    @click.option("--database", type=click.Path(path_type=Path), required=True)
    @click.option("--max-pages", type=click.IntRange(1, 30), default=30, show_default=True)
    def refresh_command(database, max_pages):
        """Fetch configured public sources. Incomplete sources retain previous data."""
        reports = asyncio.run(refresh(catalog, database, max_pages=max_pages))
        click.echo(json.dumps(reports, indent=2))
        if any(row["status"] != "complete" for row in reports):
            raise click.ClickException("Incomplete refresh; see source report above.")

    @cli.command()
    @click.option("--database", type=click.Path(path_type=Path), required=True)
    @click.option("--host", default="127.0.0.1")
    @click.option("--port", type=click.IntRange(1, 65535), default=8000)
    def serve(database, host, port):
        """Serve this catalog read-only. A missing snapshot shows an honest empty state."""
        uvicorn.run(create_app(catalog, database), host=host, port=port)

    return cli
