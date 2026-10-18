"""Cart PUT body. Keys stay in lockstep with fixtures/cart_put_request.json.

The cart PUT replaces the whole basket when it carries the cart id and its current
version. A line with quantity 0 in a partial PUT is ignored by the server, so every
change is sent as the full target list.
"""

from __future__ import annotations

from typing import Any

from merca.core.exceptions import MercaValidationError

__all__ = (
    "FORBIDDEN_PUT_KEYS",
    "REQUIRED_PUT_LINE_KEYS",
    "build_put_body",
)

REQUIRED_PUT_LINE_KEYS = ("product_id", "quantity")
FORBIDDEN_PUT_KEYS = ("item_id", "amount", "currency")


def build_put_body(
    lines: list[tuple[str, int | float]], *, cart_id: str, version: int | None
) -> dict[str, Any]:
    """Full replacement. An empty list empties the cart."""
    if not cart_id:
        raise MercaValidationError("cart id is required for a cart write")
    payload_lines: list[dict[str, Any]] = []
    for product_id, quantity in lines:
        if not str(product_id).strip():
            raise MercaValidationError("product_id is empty")
        if isinstance(quantity, bool) or not isinstance(quantity, (int, float)) or quantity <= 0:
            raise MercaValidationError("quantity in a full cart write must be > 0")
        qty: int | float = int(quantity) if float(quantity).is_integer() else quantity
        payload_lines.append({"product_id": str(product_id), "quantity": qty})
    body: dict[str, Any] = {"id": cart_id, "lines": payload_lines}
    if version is not None:
        body["version"] = version
    for key in FORBIDDEN_PUT_KEYS:
        if key in body:
            raise MercaValidationError(f"refusing cart key {key}")
    return body
