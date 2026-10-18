"""Delivered lines of past orders. Cached on disk because a delivered order never changes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from merca.core.exceptions import MercaParseError, MercaValidationError
from merca.core.paths import merca_home
from merca.http.client import TIENDA, HttpClient
from merca.models.order import DeliveredLine
from merca.models.profile import Session

__all__ = ("fetch_delivered_lines", "parse_delivered_lines")


def _num(value: object, field: str) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError) as exc:
        raise MercaParseError(f"delivered line {field} is not a number") from exc


def parse_delivered_lines(payload: dict[str, Any]) -> tuple[DeliveredLine, ...]:
    """Keep product, quantities, and price. Drop every other key."""
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise MercaParseError("delivered lines have no results list")
    lines: list[DeliveredLine] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        product = raw.get("product") if isinstance(raw.get("product"), dict) else {}
        assert isinstance(product, dict)
        product_id = str(raw.get("product_id") or product.get("id") or "")
        if not product_id:
            raise MercaParseError("delivered line missing product_id")
        block = raw.get("original_price_instructions") or product.get("price_instructions")
        price = block.get("unit_price") if isinstance(block, dict) else None
        lines.append(
            DeliveredLine(
                product_id=product_id,
                display_name=str(product.get("display_name") or product_id),
                ordered=_num(raw.get("ordered_quantity"), "ordered_quantity"),
                prepared=_num(raw.get("prepared_quantity") or 0, "prepared_quantity"),
                unit_price=_num(price, "unit_price"),
                total_eur=_num(raw.get("total_prepared_price") or 0, "total_prepared_price"),
            )
        )
    return tuple(lines)


def _cache_path(order_id: str) -> Path:
    return merca_home() / "cache" / "delivered" / f"{order_id}.json"


def _read_cache(order_id: str) -> tuple[DeliveredLine, ...] | None:
    path = _cache_path(order_id)
    if not path.is_file():
        return None
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(DeliveredLine.model_validate(row) for row in rows)


def _write_cache(order_id: str, lines: tuple[DeliveredLine, ...]) -> None:
    path = _cache_path(order_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [line.model_dump(mode="json") for line in lines]
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def fetch_delivered_lines(
    session: Session,
    warehouse: str,
    order_id: str,
    *,
    cache: bool = True,
    client: HttpClient | None = None,
) -> tuple[DeliveredLine, ...]:
    """GET /orders/{id}/lines/prepared/ with paging. cache=True only for delivered orders."""
    if not str(order_id).isdigit():
        raise MercaValidationError("order id must be digits")
    if cache:
        hit = _read_cache(order_id)
        if hit is not None:
            return hit
    http = client or HttpClient(token=session.token)
    url = f"{TIENDA}/api/customers/{session.uuid}/orders/{order_id}/lines/prepared/"
    lines: list[DeliveredLine] = []
    page = 1
    while True:
        params = {"lang": "es", "wh": warehouse}
        if page > 1:
            params["page"] = str(page)
        payload = http.request("GET", url, params=params)
        lines.extend(parse_delivered_lines(payload))
        if not payload.get("next_page") or page >= 20:
            break
        page += 1
    result = tuple(lines)
    if cache:
        _write_cache(order_id, result)
    return result
