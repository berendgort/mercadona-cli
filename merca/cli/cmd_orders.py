"""Order history, learned purchase stats, and PDF receipts. No pay, no address, no phone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.orders import save_receipt
from merca.cli.catch import run_cmd
from merca.core.access import require_profile, require_session
from merca.service.orders import history, recent_orders

__all__ = ("register",)


def _orders(
    limit: int = typer.Option(10, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Recent orders: id, status, slot, totals. Nothing else."""
    run_cmd(lambda: recent_orders(limit), as_json=json_out)


def _history(
    orders: int = typer.Option(16, "--orders", help="Most recent delivered orders to learn from."),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Per-product purchase stats from delivered orders (what was packed, not ordered)."""
    run_cmd(lambda: history(orders), as_json=json_out)


def _receipt(
    order_id: str = typer.Argument(...),
    out: str = typer.Option(..., "--out"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Download one receipt PDF. Does not print the file."""

    def _run() -> dict[str, Any]:
        profile = require_profile()
        return save_receipt(require_session(), profile.warehouse, order_id, Path(out))

    run_cmd(_run, as_json=json_out)


def register(app: typer.Typer) -> None:
    app.command("orders")(_orders)
    app.command("history")(_history)
    app.command("receipt")(_receipt)
