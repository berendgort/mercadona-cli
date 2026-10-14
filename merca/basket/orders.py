"""Recent orders and the PDF receipt. Never returns address, phone, or card."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from merca.core.exceptions import MercaNotFoundError, MercaParseError, MercaValidationError
from merca.http.client import TIENDA, HttpClient
from merca.models.order import OrderSummary
from merca.models.profile import Session

__all__ = ("list_orders", "parse_orders", "save_receipt")


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def parse_orders(payload: dict[str, Any]) -> tuple[OrderSummary, ...]:
    """Keep id, slot, status, and totals. Drop every other key."""
    results = payload.get("results")
    if not isinstance(results, list):
        raise MercaParseError("Orders response has no results list")
    rows: list[OrderSummary] = []
    for item in results:
        if not isinstance(item, dict) or item.get("id") is None:
            continue
        raw_summary = item.get("summary")
        summary: dict[str, Any] = raw_summary if isinstance(raw_summary, dict) else {}
        status = _text(item.get("status_ui") or item.get("status"))
        rows.append(
            OrderSummary(
                id=_text(item["id"]),
                status=status,
                start=_text(item.get("start_date")),
                end=_text(item.get("end_date")),
                products_eur=_text(summary.get("products") or item.get("price")),
                total_eur=_text(summary.get("total") or item.get("price")),
                products_count=int(item.get("products_count") or 0),
            )
        )
    return tuple(rows)


def list_orders(
    session: Session,
    warehouse: str,
    *,
    client: HttpClient | None = None,
) -> tuple[OrderSummary, ...]:
    http = client or HttpClient(token=session.token)
    payload = http.request(
        "GET",
        f"{TIENDA}/api/customers/{session.uuid}/orders/",
        params={"lang": "es", "wh": warehouse},
    )
    return parse_orders(payload)


def save_receipt(
    session: Session,
    warehouse: str,
    order_id: str,
    dest: Path,
    *,
    client: HttpClient | None = None,
) -> dict[str, Any]:
    """Write the PDF. The return value is path and size, not the file."""
    if not str(order_id).isdigit():
        raise MercaValidationError("order id must be digits")
    http = client or HttpClient(token=session.token)
    _status, data = http.request_bytes(
        "GET",
        f"{TIENDA}/api/customers/{session.uuid}/orders/{order_id}/receipt/",
        params={"lang": "es", "wh": warehouse},
    )
    if not data.startswith(b"%PDF"):
        raise MercaParseError("Receipt was not a PDF")
    if len(data) < 100:
        raise MercaNotFoundError("Receipt was empty")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return {"id": str(order_id), "path": str(dest), "bytes": len(data)}
