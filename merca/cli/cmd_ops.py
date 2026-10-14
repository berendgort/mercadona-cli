"""Local setup, login, and the agent recipe."""

from __future__ import annotations

from typing import Any

import typer

from merca import __version__
from merca.cli.catch import run_cmd
from merca.core.access import require_profile
from merca.core.exceptions import MercaValidationError
from merca.core.instruct import instruct_recipe
from merca.core.paths import merca_home, session_path
from merca.core.store import load_profile, load_session, save_profile, save_session
from merca.models.profile import Profile, Session

__all__ = ("register",)


def _instruct(json_out: bool = typer.Option(False, "--json")) -> None:
    run_cmd(instruct_recipe, as_json=json_out)


def _doctor(json_out: bool = typer.Option(False, "--json")) -> None:
    def _run() -> dict[str, Any]:
        profile = load_profile()
        session = load_session()
        mode_ok: bool | None = None
        path = session_path()
        if path.is_file():
            mode_ok = (path.stat().st_mode & 0o777) == 0o600
        return {
            "version": __version__,
            "home": str(merca_home()),
            "profile": profile is not None and bool(profile.warehouse),
            "postal_code": profile.postal_code if profile else None,
            "warehouse": profile.warehouse if profile else None,
            "session": session is not None,
            "session_mode_ok": mode_ok,
            "pays": False,
        }

    run_cmd(_run, as_json=json_out)


def _setup(
    cp: str = typer.Option(..., "--cp"),
    wh: str = typer.Option(..., "--wh"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, str]:
        if not (cp.isdigit() and len(cp) == 5):
            raise MercaValidationError("postal code must be 5 digits")
        if not wh.isdigit():
            raise MercaValidationError("warehouse id must be digits")
        current = load_profile() or Profile()
        save_profile(current.model_copy(update={"postal_code": cp, "warehouse": wh}))
        return {"postal_code": cp, "warehouse": wh}

    run_cmd(_run, as_json=json_out)


def _login(
    token: str = typer.Option(
        ...,
        "--token",
        help="MO-user.token from Local Storage (not Cookies).",
    ),
    uuid: str = typer.Option(
        ...,
        "--uuid",
        help="MO-user.uuid from Local Storage (not Cookies).",
    ),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Save session from Local Storage key MO-user.

    Path: tienda.mercadona.es (logged in) → F12 → Application → Local Storage
    → https://tienda.mercadona.es → click MO-user → copy token and uuid.

    Do not use the Cookies panel (__mo_da, _abck, bm_sz, …). Never pass a password.
    """

    def _run() -> dict[str, Any]:
        tok = token.strip()
        uid = uuid.strip()
        if not tok or not uid:
            raise MercaValidationError("token and uuid are required")
        if tok.startswith("<") or uid.startswith("<") or "token" == tok.lower():
            raise MercaValidationError(
                "placeholder token rejected. Paste real MO-user.token and MO-user.uuid "
                "from Local Storage (not Cookies)"
            )
        if len(tok) < 20:
            raise MercaValidationError(
                "token looks too short. Open Local Storage, key MO-user, not Cookies"
            )
        save_session(Session(token=tok, uuid=uid))
        return {"saved": True, "uuid": uid}

    run_cmd(_run, as_json=json_out)


def _block(
    product_id: str = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        profile = require_profile()
        ids = tuple(dict.fromkeys((*profile.blacklist, str(product_id))))
        save_profile(profile.model_copy(update={"blacklist": ids}))
        return {"blacklist": list(ids)}

    run_cmd(_run, as_json=json_out)


def register(app: typer.Typer) -> None:
    app.command("instruct")(_instruct)
    app.command("doctor")(_doctor)
    app.command("setup")(_setup)
    app.command("login")(_login)
    app.command("block")(_block)
