"""Delivery slots and checkout. Checkout places an order only with --confirm --yes."""

from __future__ import annotations

from datetime import date
from typing import Any

import typer

from merca.cli.catch import run_cmd
from merca.cli.cmd_policy import load_fixture
from merca.core.exceptions import MercaValidationError
from merca.core.store import load_profile, load_session
from merca.policy.checkout import checkout_plan
from merca.service.checkout import checkout, slots

__all__ = ("register",)


def _slots(json_out: bool = typer.Option(False, "--json")) -> None:
    """Delivery slots for the saved address, in local time."""
    run_cmd(slots, as_json=json_out)


def _checkout(
    day: str = typer.Option(..., "--day", help="One day or a list: LUN,MAR,MIE."),
    label: str = typer.Option(..., "--label", help="Local window, e.g. 11:00-18:00."),
    earliest: str | None = typer.Option(None, "--earliest", help="YYYY-MM-DD, local."),
    latest: str | None = typer.Option(None, "--latest", help="YYYY-MM-DD, local."),
    lead_hours: float = typer.Option(20.0, "--lead-hours"),
    confirm: bool = typer.Option(False, "--confirm", help="Place the order. Needs --yes."),
    yes: bool = typer.Option(False, "--yes"),
    allow_second: bool = typer.Option(False, "--allow-second"),
    fixture: str | None = typer.Option(None, "--fixture"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Preflight the cart and pick a slot. Stops before the order unless --confirm --yes."""

    def _run() -> dict[str, Any]:
        days = [part.strip() for part in day.split(",") if part.strip()]
        if confirm and not yes:
            raise MercaValidationError("Refusing to place an order without --yes")
        if fixture or load_session() is None:
            cart = load_fixture(fixture) if fixture else None
            return checkout_plan(days[0], label, cart=cart, profile=load_profile())
        return checkout(
            days,
            label,
            earliest=date.fromisoformat(earliest) if earliest else None,
            latest=date.fromisoformat(latest) if latest else None,
            lead_hours=lead_hours,
            confirm=confirm,
            yes=yes,
            allow_second=allow_second,
        )

    run_cmd(_run, as_json=json_out)


def register(app: typer.Typer) -> None:
    app.command("slots")(_slots)
    app.command("checkout")(_checkout)
