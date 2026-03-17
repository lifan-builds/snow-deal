from __future__ import annotations

import csv
import json
import io

from rich.console import Console
from rich.table import Table

from deal.models import Product


def sort_by_discount(products: list[Product], min_discount: float = 0) -> list[Product]:
    """Sort products by discount percentage descending, filtering by minimum."""
    filtered = [p for p in products if p.discount_pct >= min_discount]
    return sorted(filtered, key=lambda p: p.discount_pct, reverse=True)


def display_table(
    products: list[Product],
    *,
    min_discount: float = 0,
    console: Console | None = None,
) -> None:
    """Print a Rich table of products ranked by discount."""
    console = console or Console()
    ranked = sort_by_discount(products, min_discount)

    if not ranked:
        console.print("[yellow]No products found matching the criteria.[/yellow]")
        return

    table = Table(
        title=f"Deal Finder — {len(ranked)} products",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Discount", style="bold green", justify="right", width=10)
    table.add_column("Product", style="white", max_width=60)
    table.add_column("Sale Price", justify="right", width=12)
    table.add_column("Original", justify="right", width=12, style="dim")
    table.add_column("Savings", justify="right", width=12, style="green")

    for i, p in enumerate(ranked, 1):
        discount_str = f"{p.discount_pct:.0f}%" if p.discount_pct > 0 else "—"
        original_str = f"${p.original_price:,.2f}" if p.original_price else "—"
        savings_str = f"${p.savings:,.2f}" if p.savings > 0 else "—"

        discount_style = ""
        if p.discount_pct >= 30:
            discount_style = "bold red"
        elif p.discount_pct >= 15:
            discount_style = "bold yellow"

        table.add_row(
            str(i),
            f"[{discount_style}]{discount_str}[/{discount_style}]" if discount_style else discount_str,
            p.name,
            f"${p.current_price:,.2f}",
            original_str,
            savings_str,
        )

    console.print(table)

    discounted = [p for p in ranked if p.discount_pct > 0]
    console.print(
        f"\n[bold]{len(discounted)}[/bold] of [bold]{len(ranked)}[/bold] "
        f"products are on sale."
    )


def export_csv(products: list[Product], *, min_discount: float = 0) -> str:
    """Return CSV string of products ranked by discount."""
    ranked = sort_by_discount(products, min_discount)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["rank", "discount_pct", "name", "sale_price", "original_price", "savings", "url"])
    for i, p in enumerate(ranked, 1):
        writer.writerow([
            i,
            p.discount_pct,
            p.name,
            p.current_price,
            p.original_price or "",
            p.savings,
            p.url,
        ])
    return output.getvalue()


def export_json(products: list[Product], *, min_discount: float = 0) -> str:
    """Return JSON string of products ranked by discount."""
    ranked = sort_by_discount(products, min_discount)
    data = [
        {
            "rank": i,
            "discount_pct": p.discount_pct,
            "name": p.name,
            "sale_price": p.current_price,
            "original_price": p.original_price,
            "savings": p.savings,
            "url": p.url,
        }
        for i, p in enumerate(ranked, 1)
    ]
    return json.dumps(data, indent=2)
