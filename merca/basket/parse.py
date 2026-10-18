"""Parse a cart object captured from GET /cart/."""

from __future__ import annotations

from typing import Any

from merca.core.exceptions import MercaParseError
from merca.models.cart import Cart, CartLine

__all__ = ("parse_cart",)


def _line(raw: dict[str, Any]) -> CartLine:
    product = raw.get("product") if isinstance(raw.get("product"), dict) else {}
    product_id = raw.get("product_id")
    if product_id is None and isinstance(product, dict):
        product_id = product.get("id")
    if product_id is None:
        raise MercaParseError("cart line missing product_id")
    if not isinstance(product, dict):
        raise MercaParseError("cart line product is not an object")
    block = product.get("price_instructions")
    if not isinstance(block, dict) or block.get("unit_price") is None:
        raise MercaParseError(f"cart line {product_id} missing unit_price")
    try:
        price = float(block["unit_price"])
        quantity = int(raw["quantity"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MercaParseError(f"cart line {product_id} is incomplete") from exc
    name = str(product.get("display_name") or product_id)
    sources = raw.get("sources")
    return CartLine(
        product_id=str(product_id),
        quantity=quantity,
        display_name=name,
        unit_price=price,
        slug=str(product.get("slug") or ""),
        sources=tuple(str(s) for s in sources) if isinstance(sources, list) else (),
    )


def parse_cart(payload: dict[str, Any]) -> Cart:
    rows = payload.get("lines")
    if not isinstance(rows, list):
        raise MercaParseError("cart payload missing lines")
    lines = tuple(_line(row) for row in rows)
    version = payload.get("version")
    count = payload.get("products_count")
    return Cart(
        lines=lines,
        version=int(version) if isinstance(version, int) else None,
        products_count=int(count) if isinstance(count, int) else len(lines),
        cart_id=str(payload.get("id") or ""),
    )
