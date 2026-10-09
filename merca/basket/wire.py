"""Cart PUT body. Keys stay in lockstep with fixtures/cart_put_request.json."""

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


def build_put_body(lines: list[tuple[str, int]]) -> dict[str, Any]:
    """Delta PUT. Quantity 0 removes a line. Only the captured keys are sent."""
    if not lines:
        raise MercaValidationError("Cart change needs at least one line")
    payload_lines: list[dict[str, Any]] = []
    for product_id, quantity in lines:
        if not str(product_id).strip():
            raise MercaValidationError("product_id is empty")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
            raise MercaValidationError("quantity must be a whole number >= 0")
        payload_lines.append({"product_id": str(product_id), "quantity": quantity})
    body: dict[str, Any] = {"lines": payload_lines}
    for key in FORBIDDEN_PUT_KEYS:
        if key in body:
            raise MercaValidationError(f"refusing cart key {key}")
    return body
