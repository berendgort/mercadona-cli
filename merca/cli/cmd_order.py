"""Read one order, or edit a confirmed one. Edits need --yes. Never pays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.fill import parse_fill
from merca.cli.catch import run_cmd
from merca.core.exceptions import MercaValidationError
from merca.service.orders import order_edit, order_show

__all__ = ("order_app",)


order_app = typer.Typer(help="One order: show its lines, or edit it before the deadline.")


@order_app.command("show")
def _show(
    order_id: str = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Confirmed: editable lines and deadline. Delivered: what was actually packed."""
    run_cmd(lambda: order_show(order_id), as_json=json_out)


@order_app.command("edit")
def _edit(
    order_id: str = typer.Argument(...),
    src: str = typer.Option(..., "--file", help="Lines of 'product_id qty'. 0 removes."),
    yes: bool = typer.Option(False, "--yes", help="Without it, print the diff and send nothing."),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Set absolute quantities. New ids are added. Unlisted lines stay."""

    def _run() -> dict[str, Any]:
        path = Path(src)
        if not path.is_file():
            raise MercaValidationError(f"edit file not found: {src}")
        return order_edit(order_id, parse_fill(path.read_text(encoding="utf-8")), yes=yes)

    run_cmd(_run, as_json=json_out)
