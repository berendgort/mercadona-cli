"""Print the JSON envelope and set the exit code."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import typer

from merca.cli.console import console
from merca.core.envelope import error_payload, success_payload

__all__ = ("emit", "run_cmd")


def emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False))
        return
    if payload.get("ok"):
        console.print(payload.get("data"))
        return
    console.print(f"[red]{payload.get('error')}[/red]")


def run_cmd(fn: Callable[[], Any], *, as_json: bool) -> None:
    try:
        emit(success_payload(fn()), as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        emit(error_payload(exc), as_json=as_json)
        raise typer.Exit(code=1) from exc
