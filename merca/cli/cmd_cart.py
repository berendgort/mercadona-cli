"""Cart read and delta writes. Writes require --yes."""

from __future__ import annotations

from typing import Any

import typer

from merca.basket.cart import fetch_cart, put_lines
from merca.cli.catch import run_cmd
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaValidationError

__all__ = ("cart_app",)


cart_app = typer.Typer(help="Read or change the basket. Changes need --yes.")


@cart_app.callback(invoke_without_command=True)
def _show(
    ctx: typer.Context,
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return

    def _run() -> dict[str, Any]:
        profile = require_profile()
        cart = fetch_cart(require_session(), profile.warehouse)
        return cart.model_dump(mode="json")

    run_cmd(_run, as_json=json_out)


@cart_app.command("add")
def _add(
    product_id: str = typer.Argument(...),
    qty: int = typer.Option(1, "--qty"),
    yes: bool = typer.Option(False, "--yes"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        if not yes:
            raise MercaValidationError("Refusing to change the cart without --yes")
        profile = require_profile()
        cart = put_lines(require_session(), profile.warehouse, [(product_id, qty)])
        return cart.model_dump(mode="json")

    run_cmd(_run, as_json=json_out)


@cart_app.command("remove")
def _remove(
    product_id: str = typer.Argument(...),
    yes: bool = typer.Option(False, "--yes"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        if not yes:
            raise MercaValidationError("Refusing to change the cart without --yes")
        profile = require_profile()
        cart = put_lines(require_session(), profile.warehouse, [(product_id, 0)])
        return cart.model_dump(mode="json")

    run_cmd(_run, as_json=json_out)
