"""Authenticated cart read and verified full-list writes."""

from __future__ import annotations

from typing import Any

from merca.basket.parse import parse_cart
from merca.basket.wire import build_put_body
from merca.core.exceptions import MercaHTTPError, MercaValidationError
from merca.http.client import TIENDA, HttpClient
from merca.models.cart import Cart
from merca.models.profile import Session
from merca.policy.preflight import line_spend

__all__ = ("apply_changes", "fetch_cart", "public_cart", "put_lines", "replace_cart")


def _url(customer_id: str) -> str:
    return f"{TIENDA}/api/customers/{customer_id}/cart/"


def public_cart(cart: Cart) -> dict[str, Any]:
    """Cart plus the line-price spend. No account fields."""
    payload = cart.model_dump(mode="json")
    payload["item_count"] = len(cart.lines)
    payload["spend"] = line_spend(cart)
    return payload


def fetch_cart(session: Session, warehouse: str, *, client: HttpClient | None = None) -> Cart:
    http = client or HttpClient(token=session.token)
    payload = http.request("GET", _url(session.uuid), params={"lang": "es", "wh": warehouse})
    return parse_cart(payload)


def apply_changes(cart: Cart, changes: list[tuple[str, int]]) -> list[tuple[str, int | float]]:
    """Absolute quantities on top of the current cart. 0 removes. Order is kept."""
    target: dict[str, int | float] = {line.product_id: line.quantity for line in cart.lines}
    for product_id, quantity in changes:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise MercaValidationError("quantity must be a whole number >= 0")
        if quantity == 0:
            target.pop(str(product_id), None)
        else:
            target[str(product_id)] = quantity
    return list(target.items())


def _same(cart: Cart, lines: list[tuple[str, int | float]]) -> bool:
    got = {line.product_id: float(line.quantity) for line in cart.lines}
    return got == {pid: float(qty) for pid, qty in lines}


def replace_cart(
    session: Session,
    warehouse: str,
    lines: list[tuple[str, int | float]],
    *,
    client: HttpClient | None = None,
) -> Cart:
    """Write the full list, re-read, and retry once on a version race."""
    http = client or HttpClient(token=session.token)
    for _attempt in range(2):
        current = fetch_cart(session, warehouse, client=http)
        body = build_put_body(lines, cart_id=current.cart_id, version=current.version)
        http.request("PUT", _url(session.uuid), params={"lang": "es", "wh": warehouse}, body=body)
        saved = fetch_cart(session, warehouse, client=http)
        if _same(saved, lines):
            return saved
    raise MercaHTTPError("Cart write did not stick (version race). Nothing else was changed")


def put_lines(
    session: Session,
    warehouse: str,
    changes: list[tuple[str, int]],
    *,
    client: HttpClient | None = None,
) -> Cart:
    """Set quantities for some products and keep the rest."""
    http = client or HttpClient(token=session.token)
    current = fetch_cart(session, warehouse, client=http)
    return replace_cart(session, warehouse, apply_changes(current, changes), client=http)
