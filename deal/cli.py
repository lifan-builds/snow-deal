from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console

from deal.display import display_table, export_csv, export_json
from deal.scraper import scrape

console = Console()


@click.command()
@click.argument("url")
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(["table", "csv", "json"]),
    default="table",
    help="Output format.",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Write output to a file instead of stdout.",
)
@click.option(
    "--min-discount", "-m",
    type=float,
    default=0,
    help="Only show products with at least this discount %%.",
)
@click.option(
    "--delay", "-d",
    type=float,
    default=1.0,
    help="Seconds to wait between page requests.",
)
@click.option(
    "--max-pages",
    type=int,
    default=50,
    help="Maximum number of pages to scrape.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def cli(
    url: str,
    output_format: str,
    output: str | None,
    min_discount: float,
    delay: float,
    max_pages: int,
    verbose: bool,
) -> None:
    """Scrape an e-commerce listing page and rank products by discount percentage."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    with console.status("[bold cyan]Scraping product listings…", spinner="dots"):
        try:
            products = asyncio.run(scrape(url, delay=delay, max_pages=max_pages))
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    if not products:
        console.print("[yellow]No products found on the page.[/yellow]")
        sys.exit(0)

    console.print(f"[dim]Scraped {len(products)} products total.[/dim]\n")

    if output_format == "table":
        display_table(products, min_discount=min_discount, console=console)
    elif output_format == "csv":
        result = export_csv(products, min_discount=min_discount)
        _write_output(result, output)
    elif output_format == "json":
        result = export_json(products, min_discount=min_discount)
        _write_output(result, output)


def _write_output(content: str, path: str | None) -> None:
    if path:
        Path(path).write_text(content)
        console.print(f"[green]Written to {path}[/green]")
    else:
        console.print(content)
