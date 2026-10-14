"""Cart read and delta writes. Writes require --yes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from merca.basket.cart import fetch_cart, public_cart, put_lines
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


def _parse_fill(text: str) -> list[tuple[str, int]]:
    parsed: list[tuple[str, int]] = []
    for raw in text.splitlines():
        row = raw.split("#", 1)[0].strip()
        if not row:
            continue
        parts = row.split()
        if len(parts) != 2 or not parts[1].isdigit():
            raise MercaValidationError(f"expected 'product_id qty', got {raw!r}")
        parsed.append((parts[0], int(parts[1])))
    if not parsed:
        raise MercaValidationError("fill file has no lines")
    return parsed


@cart_app.command("fill")
def _fill(
    src: str = typer.Option(..., "--file", help="Lines of 'product_id qty'. # comments allowed."),
    yes: bool = typer.Option(False, "--yes"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Set many quantities in one PUT. Needs --yes."""

    def _run() -> dict[str, Any]:
        if not yes:
            raise MercaValidationError("Refusing to change the cart without --yes")
        path = Path(src)
        if not path.is_file():
            raise MercaValidationError(f"fill file not found: {src}")
        profile = require_profile()
        lines = _parse_fill(path.read_text(encoding="utf-8"))
        cart = put_lines(require_session(), profile.warehouse, lines)
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
