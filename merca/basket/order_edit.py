"""Edit the lines of a confirmed order before its change deadline.

The web app saves an edited order with one PUT of the full line list to
/orders/{id}/cart/. This module never deletes an order and never pays.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from merca.core.exceptions import MercaNotFoundError, MercaParseError, MercaValidationError
from merca.http.client import TIENDA, HttpClient
from merca.models.order import OrderCart, OrderLine
from merca.models.product import Product
from merca.models.profile import Session

__all__ = (
    "SOURCE_SEARCH",
    "EditWindow",
    "build_order_put_body",
    "fetch_edit_window",
    "fetch_order_cart",
    "parse_edit_window",
    "parse_order_cart",
    "plan_order_edit",
    "put_order_cart",
)

EditWindow = tuple[str, datetime]
# Line source code the web app sends for a product added from search.
SOURCE_SEARCH = "+SA"


def _order_url(customer_id: str, order_id: str) -> str:
    if not str(order_id).isdigit():
        raise MercaValidationError("order id must be digits")
    return f"{TIENDA}/api/customers/{customer_id}/orders/{order_id}/"


def _line(raw: dict[str, Any]) -> OrderLine:
    product = raw.get("product")
    if not isinstance(product, dict):
        raise MercaParseError("order line has no product object")
    block = product.get("price_instructions")
    if not isinstance(block, dict) or block.get("unit_price") is None:
        raise MercaParseError("order line missing unit_price")
    try:
        line_id = int(raw["id"])
        quantity = float(raw["quantity"])
        price = float(block["unit_price"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MercaParseError("order line is incomplete") from exc
    product_id = str(raw.get("product_id") or product.get("id") or "")
    if not product_id:
        raise MercaParseError("order line missing product_id")
    sources = raw.get("sources")
    return OrderLine(
        line_id=line_id,
        product_id=product_id,
        quantity=quantity,
        display_name=str(product.get("display_name") or product_id),
        unit_price=price,
        sources=tuple(str(s) for s in sources) if isinstance(sources, list) else (),
    )


def parse_order_cart(order_id: str, payload: dict[str, Any]) -> OrderCart:
    rows = payload.get("lines")
    cart_id = payload.get("id")
    if not isinstance(rows, list) or not cart_id:
        raise MercaParseError("order cart needs id and lines")
    version = payload.get("version")
    return OrderCart(
        order_id=str(order_id),
        cart_id=str(cart_id),
        version=version if isinstance(version, int) else None,
        lines=tuple(_line(row) for row in rows if isinstance(row, dict)),
    )


def parse_edit_window(payload: dict[str, Any]) -> EditWindow:
    """Status and change deadline. Every other order key is dropped."""
    status = str(payload.get("status_ui") or "")
    raw = payload.get("changes_until")
    if not isinstance(raw, str) or not raw:
        raise MercaParseError("order has no changes_until")
    try:
        until = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MercaParseError("changes_until is not ISO time") from exc
    return status, until


def fetch_edit_window(
    session: Session, warehouse: str, order_id: str, *, client: HttpClient | None = None
) -> EditWindow:
    http = client or HttpClient(token=session.token)
    payload = http.request(
        "GET", _order_url(session.uuid, order_id), params={"lang": "es", "wh": warehouse}
    )
    return parse_edit_window(payload)


def fetch_order_cart(
    session: Session, warehouse: str, order_id: str, *, client: HttpClient | None = None
) -> OrderCart:
    http = client or HttpClient(token=session.token)
    payload = http.request(
        "GET",
        _order_url(session.uuid, order_id) + "cart/",
        params={"lang": "es", "wh": warehouse},
    )
    return parse_order_cart(order_id, payload)


def plan_order_edit(
    cart: OrderCart,
    changes: list[tuple[str, int]],
    *,
    window: EditWindow,
    now: datetime | None = None,
    new_products: Mapping[str, Product] | None = None,
) -> OrderCart:
    """Apply absolute quantities. 0 removes a line. Unlisted lines stay as they are.

    A product not yet in the order is appended when new_products holds its catalog row.
    """
    status, until = window
    if status != "confirmed":
        raise MercaValidationError(f"order status is {status!r}, only confirmed orders can change")
    moment = now or datetime.now(timezone.utc)
    if moment >= until:
        raise MercaValidationError(f"change deadline passed ({until.isoformat()})")
    targets: dict[str, int] = {}
    for product_id, wanted in changes:
        if product_id in targets:
            raise MercaValidationError(f"product {product_id} listed twice")
        targets[product_id] = wanted
    known = {line.product_id for line in cart.lines}
    catalog = new_products or {}
    unknown = sorted(pid for pid in set(targets) - known if pid not in catalog)
    if unknown:
        raise MercaNotFoundError(f"not in this order and not looked up: {', '.join(unknown)}")
    kept: list[OrderLine] = []
    for line in cart.lines:
        target = targets.get(line.product_id)
        if target is None:
            kept.append(line)
        elif target > 0:
            kept.append(line.model_copy(update={"quantity": float(target)}))
    for product_id, target in targets.items():
        if product_id in known or target <= 0:
            continue
        product = catalog[product_id]
        kept.append(
            OrderLine(
                line_id=0,
                product_id=product.id,
                quantity=float(target),
                display_name=product.display_name,
                unit_price=product.unit_price,
                sources=(SOURCE_SEARCH,),
            )
        )
    if not kept:
        raise MercaValidationError("Refusing to remove every line. That cancels the order")
    return cart.model_copy(update={"lines": tuple(kept)})


def build_order_put_body(cart: OrderCart) -> dict[str, Any]:
    """Full line list, in the web app shape: {"cart": {id, version?, lines}}."""
    lines: list[dict[str, Any]] = []
    for line in cart.lines:
        quantity: float | int = line.quantity
        if float(quantity).is_integer():
            quantity = int(quantity)
        row: dict[str, Any] = {
            "quantity": quantity,
            "product_id": line.product_id,
            "sources": list(line.sources),
        }
        if line.line_id:
            row = {"id": line.line_id, **row}
        lines.append(row)
    inner: dict[str, Any] = {"id": cart.cart_id, "lines": lines}
    if cart.version:
        inner["version"] = cart.version
    return {"cart": inner}


def put_order_cart(
    session: Session, warehouse: str, cart: OrderCart, *, client: HttpClient | None = None
) -> dict[str, Any]:
    http = client or HttpClient(token=session.token)
    return http.request(
        "PUT",
        _order_url(session.uuid, cart.order_id) + "cart/",
        params={"lang": "es", "wh": warehouse},
        body=build_order_put_body(cart),
    )
