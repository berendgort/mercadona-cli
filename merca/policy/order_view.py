"""Readable views of an order cart: line table, spend, and before/after diff. Pure."""

from __future__ import annotations

from typing import Any

from merca.models.order import OrderCart

__all__ = ("order_diff", "public_order_cart")


def _spend(cart: OrderCart) -> float:
    return round(sum(line.unit_price * line.quantity for line in cart.lines), 2)


def public_order_cart(cart: OrderCart) -> dict[str, Any]:
    rows = [
        {
            "product_id": line.product_id,
            "quantity": line.quantity,
            "display_name": line.display_name,
            "unit_price": line.unit_price,
        }
        for line in cart.lines
    ]
    return {"order_id": cart.order_id, "lines": rows, "count": len(rows), "spend": _spend(cart)}


def order_diff(before: OrderCart, after: OrderCart) -> dict[str, Any]:
    """Every product whose quantity moved, including products added to the order."""
    old = {line.product_id: line for line in before.lines}
    new = {line.product_id: line for line in after.lines}
    changed: list[dict[str, Any]] = []
    for pid in [*old, *(p for p in new if p not in old)]:
        was = old[pid].quantity if pid in old else 0.0
        now = new[pid].quantity if pid in new else 0.0
        if was != now:
            name = (old.get(pid) or new[pid]).display_name
            changed.append({"product_id": pid, "display_name": name, "from": was, "to": now})
    return {
        "changed": changed,
        "lines_before": len(before.lines),
        "lines_after": len(after.lines),
        "spend_before": _spend(before),
        "spend_after": _spend(after),
    }
