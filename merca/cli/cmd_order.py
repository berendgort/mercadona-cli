"""Read or edit the lines of one confirmed order. Edits need --yes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.fill import parse_fill
from merca.basket.order_edit import (
    fetch_edit_window,
    fetch_order_cart,
    order_diff,
    plan_order_edit,
    public_order_cart,
    put_order_cart,
)
from merca.cli.catch import run_cmd
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaValidationError
from merca.models.order import OrderCart

__all__ = ("order_app",)


order_app = typer.Typer(help="Lines of one confirmed order. Edit needs --yes. Never pays.")


@order_app.command("show")
def _show(
    order_id: str = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Lines, spend, and the change deadline."""

    def _run() -> dict[str, Any]:
        profile = require_profile()
        session = require_session()
        status, until = fetch_edit_window(session, profile.warehouse, order_id)
        cart = fetch_order_cart(session, profile.warehouse, order_id)
        return {**public_order_cart(cart), "status": status, "changes_until": until.isoformat()}

    run_cmd(_run, as_json=json_out)


@order_app.command("edit")
def _edit(
    order_id: str = typer.Argument(...),
    src: str = typer.Option(..., "--file", help="Lines of 'product_id qty'. 0 removes."),
    yes: bool = typer.Option(False, "--yes", help="Without it, print the diff and send nothing."),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Set absolute quantities on existing lines. Unlisted lines stay."""

    def _run() -> dict[str, Any]:
        path = Path(src)
        if not path.is_file():
            raise MercaValidationError(f"edit file not found: {src}")
        changes = parse_fill(path.read_text(encoding="utf-8"))
        profile = require_profile()
        session = require_session()
        window = fetch_edit_window(session, profile.warehouse, order_id)
        before = fetch_order_cart(session, profile.warehouse, order_id)
        after = plan_order_edit(before, changes, window=window)
        diff = order_diff(before, after)
        if not yes:
            return {**diff, "sent": False, "changes_until": window[1].isoformat()}
        put_order_cart(session, profile.warehouse, after)
        saved = fetch_order_cart(session, profile.warehouse, order_id)
        return {**order_diff(before, saved), "sent": True, "matches_plan": _same(after, saved)}

    run_cmd(_run, as_json=json_out)


def _same(planned: OrderCart, saved: OrderCart) -> bool:
    want = {line.product_id: line.quantity for line in planned.lines}
    got = {line.product_id: line.quantity for line in saved.lines}
    return want == got
