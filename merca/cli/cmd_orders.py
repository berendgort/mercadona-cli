"""Order history and PDF receipts. No pay, no address, no phone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.orders import list_orders, save_receipt
from merca.cli.catch import run_cmd
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaValidationError

__all__ = ("register",)


def _orders(
    limit: int = typer.Option(10, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Recent orders: id, status, slot, totals. Nothing else."""

    def _run() -> dict[str, Any]:
        if limit < 1 or limit > 48:
            raise MercaValidationError("limit must be 1..48")
        profile = require_profile()
        rows = list_orders(require_session(), profile.warehouse)
        chosen = rows[:limit]
        return {"orders": [row.model_dump(mode="json") for row in chosen], "count": len(chosen)}

    run_cmd(_run, as_json=json_out)


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
    app.command("receipt")(_receipt)
