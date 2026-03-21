"""Click CLI for the deal aggregator."""

from __future__ import annotations

import asyncio
import logging

import click
from rich.console import Console
from rich.table import Table

from aggregator.db import init_db, query_deals, upsert_deals
from aggregator.scraper import scrape_all

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def cli(verbose: bool) -> None:
    """snow-deals aggregator — scrape and rank ski/snowboard deals."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.option("--delay", "-d", type=float, default=1.0, help="Delay between requests.")
@click.option("--max-pages", type=int, default=10, help="Max pages per store.")
def refresh(delay: float, max_pages: int) -> None:
    """Scrape all stores and update the database."""
    async def _run() -> None:
        await init_db()
        with console.status("[bold cyan]Scraping all stores...", spinner="dots"):
            deals = await scrape_all(delay=delay, max_pages=max_pages)
        console.print(f"[dim]Scraped {len(deals)} deals total.[/dim]")

        if deals:
            count = await upsert_deals(deals)
            console.print(f"[green]Saved {count} deals to database.[/green]")

    asyncio.run(_run())


@cli.command()
@click.option("--category", "-c", default=None, help="Filter by category.")
@click.option("--store", "-s", default=None, help="Filter by store name.")
@click.option("--min-discount", "-m", type=float, default=0, help="Minimum discount %%.")
@click.option("--limit", "-l", type=int, default=50, help="Max results.")
def deals(category: str | None, store: str | None, min_discount: float, limit: int) -> None:
    """Query deals from the database."""
    async def _run() -> None:
        await init_db()
        results = await query_deals(
            category=category, store=store, min_discount=min_discount, limit=limit
        )

        if not results:
            console.print("[yellow]No deals found matching criteria.[/yellow]")
            return

        table = Table(title=f"Top Deals — {len(results)} results", show_lines=True)
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Discount", style="bold green", justify="right", width=10)
        table.add_column("Product", style="white", max_width=50)
        table.add_column("Store", style="cyan", width=20)
        table.add_column("Price", justify="right", width=10)
        table.add_column("Category", style="dim", width=12)

        for i, d in enumerate(results, 1):
            table.add_row(
                str(i),
                f"{d.discount_pct:.0f}%",
                d.name,
                d.store,
                f"${d.current_price:,.2f}",
                d.category or "—",
            )

        console.print(table)

    asyncio.run(_run())
