"""Cart read and delta writes. Writes require --yes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.cart import fetch_cart, public_cart, put_lines, replace_cart
from merca.basket.fill import parse_fill
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
        return public_cart(cart)

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
        return public_cart(cart)

    run_cmd(_run, as_json=json_out)


@cart_app.command("fill")
def _fill(
    src: str = typer.Option(..., "--file", help="Lines of 'product_id qty'. # comments allowed."),
    replace: bool = typer.Option(
        False, "--replace", help="Make the cart exactly the file. Other lines are removed."
    ),
    yes: bool = typer.Option(False, "--yes"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Set many quantities in one verified write. Needs --yes."""

    def _run() -> dict[str, Any]:
        if not yes:
            raise MercaValidationError("Refusing to change the cart without --yes")
        path = Path(src)
        if not path.is_file():
            raise MercaValidationError(f"fill file not found: {src}")
        profile = require_profile()
        lines = parse_fill(path.read_text(encoding="utf-8"))
        session = require_session()
        if replace:
            wanted: list[tuple[str, int | float]] = [(pid, q) for pid, q in lines if q > 0]
            cart = replace_cart(session, profile.warehouse, wanted)
        else:
            cart = put_lines(session, profile.warehouse, lines)
        return public_cart(cart)

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
        return public_cart(cart)

    run_cmd(_run, as_json=json_out)


@cart_app.command("clear")
def _clear(
    yes: bool = typer.Option(False, "--yes"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Empty the basket. Needs --yes."""

    def _run() -> dict[str, Any]:
        if not yes:
            raise MercaValidationError("Refusing to change the cart without --yes")
        profile = require_profile()
        return public_cart(replace_cart(require_session(), profile.warehouse, []))

    run_cmd(_run, as_json=json_out)
