"""Order use cases: show, edit, history."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from merca.basket.delivered import fetch_delivered_lines
from merca.basket.order_edit import (
    fetch_edit_window,
    fetch_order_cart,
    plan_order_edit,
    put_order_cart,
)
from merca.basket.orders import list_orders
from merca.catalog.search import get_product
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaValidationError
from merca.models.order import OrderCart
from merca.policy.history import DeliveredOrder, build_history
from merca.policy.order_view import order_diff, public_order_cart
from merca.policy.slot_pick import MADRID

__all__ = ("history", "order_edit", "order_show", "recent_orders")


def recent_orders(limit: int) -> dict[str, Any]:
    if limit < 1 or limit > 48:
        raise MercaValidationError("limit must be 1..48")
    profile = require_profile()
    rows = list_orders(require_session(), profile.warehouse)[:limit]
    return {"orders": [row.model_dump(mode="json") for row in rows], "count": len(rows)}


def order_show(order_id: str) -> dict[str, Any]:
    """Confirmed: editable lines and deadline. Otherwise: what was actually packed."""
    profile = require_profile()
    session = require_session()
    status, until = fetch_edit_window(session, profile.warehouse, order_id)
    if status == "confirmed":
        cart = fetch_order_cart(session, profile.warehouse, order_id)
        return {**public_order_cart(cart), "status": status, "changes_until": until.isoformat()}
    lines = fetch_delivered_lines(session, profile.warehouse, order_id, cache=status == "delivered")
    rows = [line.model_dump(mode="json") for line in lines]
    return {
        "order_id": order_id,
        "status": status,
        "lines": rows,
        "count": len(rows),
        "spend": round(sum(line.total_eur for line in lines), 2),
        "shortages": [row for row in rows if row["prepared"] < row["ordered"]],
    }


def _same(planned: OrderCart, saved: OrderCart) -> bool:
    want = {line.product_id: line.quantity for line in planned.lines}
    got = {line.product_id: line.quantity for line in saved.lines}
    return want == got


def order_edit(order_id: str, changes: list[tuple[str, int]], *, yes: bool) -> dict[str, Any]:
    """Absolute quantities; 0 removes; new ids are added. Dry run unless yes."""
    profile = require_profile()
    session = require_session()
    window = fetch_edit_window(session, profile.warehouse, order_id)
    before = fetch_order_cart(session, profile.warehouse, order_id)
    known = {line.product_id for line in before.lines}
    new = {
        pid: get_product(pid, profile.warehouse)
        for pid, qty in changes
        if qty > 0 and pid not in known
    }
    after = plan_order_edit(before, changes, window=window, new_products=new)
    if not yes:
        return {**order_diff(before, after), "sent": False, "changes_until": window[1].isoformat()}
    put_order_cart(session, profile.warehouse, after)
    saved = fetch_order_cart(session, profile.warehouse, order_id)
    return {**order_diff(before, saved), "sent": True, "matches_plan": _same(after, saved)}


def history(orders: int) -> dict[str, Any]:
    """Per-product stats over the most recent delivered orders."""
    if orders < 1 or orders > 48:
        raise MercaValidationError("orders must be 1..48")
    profile = require_profile()
    session = require_session()
    rows = [row for row in list_orders(session, profile.warehouse) if row.status == "delivered"]
    rows.sort(key=lambda row: row.start, reverse=True)
    picked: list[DeliveredOrder] = []
    for row in rows[:orders]:
        day = datetime.fromisoformat(row.start.replace("Z", "+00:00")).astimezone(MADRID)
        picked.append((day.date(), fetch_delivered_lines(session, profile.warehouse, row.id)))
    return build_history(picked).model_dump(mode="json")
