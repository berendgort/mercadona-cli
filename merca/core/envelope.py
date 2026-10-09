"""JSON envelope shared by the CLI and MCP."""

from __future__ import annotations

from typing import Any

from merca.core.errors import classify_error
from merca.core.exceptions import MercaAmbiguousError, MercaAuthError

__all__ = (
    "API_VERSION",
    "error_payload",
    "success_payload",
)

API_VERSION = 1

_LOGIN = (
    "merca login --token <MO-user.token> --uuid <MO-user.uuid> --json. "
    "Copy both from the tienda site local storage. Never paste a password."
)


def success_payload(data: Any) -> dict[str, Any]:
    return {"ok": True, "api_version": API_VERSION, "data": data}


def error_payload(exc: BaseException) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "api_version": API_VERSION,
        "error": str(exc),
        **classify_error(exc).as_fields(),
    }
    if isinstance(exc, MercaAmbiguousError):
        payload["candidates"] = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in exc.candidates
        ]
    if isinstance(exc, MercaAuthError):
        payload["human_fix"] = _LOGIN
    return payload
