"""Authenticated cart read and delta write."""

from __future__ import annotations

from typing import Any

from merca.basket.parse import parse_cart
from merca.basket.wire import build_put_body
from merca.http.client import TIENDA, HttpClient
from merca.models.cart import Cart
from merca.models.profile import Session
from merca.policy.preflight import line_spend

__all__ = ("fetch_cart", "public_cart", "put_lines")


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
    payload = http.request(
        "GET",
        _url(session.uuid),
        params={"lang": "es", "wh": warehouse},
    )
    return parse_cart(payload)


def put_lines(
    session: Session,
    warehouse: str,
    lines: list[tuple[str, int]],
    *,
    client: HttpClient | None = None,
) -> Cart:
    body: dict[str, Any] = build_put_body(lines)
    http = client or HttpClient(token=session.token)
    payload = http.request(
        "PUT",
        _url(session.uuid),
        params={"lang": "es", "wh": warehouse},
        body=body,
    )
    return parse_cart(payload)
