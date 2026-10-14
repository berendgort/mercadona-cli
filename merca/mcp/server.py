"""FastMCP tools. Does not import the CLI package."""

from __future__ import annotations

from typing import Any

from merca.basket.cart import fetch_cart, public_cart, put_lines
from merca.basket.orders import list_orders
from merca.catalog.search import get_product, search_products
from merca.core.access import require_profile, require_session
from merca.core.envelope import error_payload, success_payload
from merca.core.exceptions import MercaValidationError
from merca.core.instruct import instruct_recipe
from merca.core.store import load_profile, load_session
from merca.models.profile import Profile
from merca.policy.checkout import checkout_plan
from merca.policy.slot import check_delivery_slot

__all__ = ("build_server",)


def _wrap(fn: Any) -> dict[str, Any]:
    try:
        return success_payload(fn())
    except Exception as exc:  # noqa: BLE001
        return error_payload(exc)


def build_server() -> Any:
    from fastmcp import FastMCP

    mcp = FastMCP("merca")

    @mcp.tool()
    def instruct() -> dict[str, Any]:
        return _wrap(instruct_recipe)

    @mcp.tool()
    def search(query: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            profile = require_profile()
            return search_products(query, profile.warehouse).model_dump(mode="json")

        return _wrap(_run)

    @mcp.tool()
    def product(product_id: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            profile = require_profile()
            return get_product(product_id, profile.warehouse).model_dump(mode="json")

        return _wrap(_run)

    @mcp.tool()
    def slot(day: str, label: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            ok, errors = check_delivery_slot(day, label)
            if not ok:
                raise MercaValidationError("; ".join(errors))
            return {"day": day, "label": label, "ok": True}

        return _wrap(_run)

    @mcp.tool()
    def checkout(day: str, label: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            profile = load_profile() or Profile()
            session = load_session()
            cart = None
            if session is not None and profile.warehouse:
                cart = fetch_cart(session, profile.warehouse)
            return checkout_plan(day, label, cart=cart, profile=profile)

        return _wrap(_run)

    @mcp.tool()
    def orders(limit: int = 10) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if limit < 1 or limit > 48:
                raise MercaValidationError("limit must be 1..48")
            profile = require_profile()
            rows = list_orders(require_session(), profile.warehouse)[:limit]
            dumped = [row.model_dump(mode="json") for row in rows]
            return {"orders": dumped, "count": len(dumped)}

        return _wrap(_run)

    @mcp.tool()
    def cart_add(product_id: str, qty: int = 1, yes: bool = False) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if not yes:
                raise MercaValidationError("Refusing to change the cart without yes=true")
            profile = require_profile()
            cart = put_lines(require_session(), profile.warehouse, [(product_id, qty)])
            return public_cart(cart)

        return _wrap(_run)

    @mcp.tool()
    def cart_show() -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            profile = require_profile()
            return public_cart(fetch_cart(require_session(), profile.warehouse))

        return _wrap(_run)

    return mcp
