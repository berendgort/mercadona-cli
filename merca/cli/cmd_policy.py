"""Slot check, basket preflight, and checkout that stops before pay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from merca.basket.cart import fetch_cart
from merca.basket.parse import parse_cart
from merca.cli.catch import run_cmd
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaValidationError
from merca.core.store import load_profile
from merca.models.profile import Profile
from merca.policy.checkout import checkout_plan
from merca.policy.preflight import run_preflight
from merca.policy.slot import check_delivery_slot

__all__ = ("register",)


def _load_fixture(fixture: str) -> Any:
    path = Path(fixture)
    if not path.is_file():
        raise MercaValidationError(f"fixture not found: {fixture}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MercaValidationError("fixture must be a JSON object")
    return parse_cart(payload)


def _slot(
    day: str = typer.Option(..., "--day"),
    label: str = typer.Option(..., "--label"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        ok, errors = check_delivery_slot(day, label)
        if not ok:
            raise MercaValidationError("; ".join(errors))
        return {"day": day, "label": label, "ok": True}

    run_cmd(_run, as_json=json_out)


def _preflight(
    fixture: str | None = typer.Option(None, "--fixture"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        if fixture:
            cart = _load_fixture(fixture)
        else:
            profile = require_profile()
            cart = fetch_cart(require_session(), profile.warehouse)
        report = run_preflight(cart, load_profile() or Profile())
        if not report.ok:
            raise MercaValidationError("; ".join(report.errors))
        return report.model_dump(mode="json")

    run_cmd(_run, as_json=json_out)


def _checkout(
    day: str = typer.Option(..., "--day"),
    label: str = typer.Option(..., "--label"),
    fixture: str | None = typer.Option(None, "--fixture"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        cart = _load_fixture(fixture) if fixture else None
        return checkout_plan(day, label, cart=cart, profile=load_profile())

    run_cmd(_run, as_json=json_out)


def register(app: typer.Typer) -> None:
    app.command("slot")(_slot)
    app.command("preflight")(_preflight)
    app.command("checkout")(_checkout)
