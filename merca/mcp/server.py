"""FastMCP tools. Same use cases as the CLI, via merca.service. Does not import the CLI."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from merca.basket.cart import fetch_cart, public_cart, put_lines, replace_cart
from merca.basket.fill import parse_fill
from merca.catalog.search import get_product, search_products
from merca.core.access import require_profile, require_session
from merca.core.envelope import error_payload, success_payload
from merca.core.exceptions import MercaValidationError
from merca.core.instruct import instruct_recipe
from merca.policy.slot import check_delivery_slot
from merca.service import checkout as checkout_service
from merca.service import orders as order_service

__all__ = ("build_server",)


def _wrap(fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        return success_payload(fn())
    except Exception as exc:  # noqa: BLE001
        return error_payload(exc)


def _need_yes(yes: bool) -> None:
    if not yes:
        raise MercaValidationError("Refusing to write without yes=true")


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
    def slots() -> dict[str, Any]:
        return _wrap(checkout_service.slots)

    @mcp.tool()
    def checkout(
        days: str = "LUN,MAR,MIE",
        label: str = "11:00-18:00",
        earliest: str = "",
        latest: str = "",
        confirm: bool = False,
        yes: bool = False,
    ) -> dict[str, Any]:
        """Preflight and pick a slot. Places the order only with confirm=true and yes=true."""
        return _wrap(
            lambda: checkout_service.checkout(
                [d.strip() for d in days.split(",") if d.strip()],
                label,
                earliest=date.fromisoformat(earliest) if earliest else None,
                latest=date.fromisoformat(latest) if latest else None,
                confirm=confirm,
                yes=yes,
            )
        )

    @mcp.tool()
    def orders(limit: int = 10) -> dict[str, Any]:
        return _wrap(lambda: order_service.recent_orders(limit))

    @mcp.tool()
    def order_show(order_id: str) -> dict[str, Any]:
        return _wrap(lambda: order_service.order_show(order_id))

    @mcp.tool()
    def order_edit(order_id: str, lines: str, yes: bool = False) -> dict[str, Any]:
        """lines: 'product_id qty' per row, 0 removes. Dry run unless yes=true."""
        return _wrap(lambda: order_service.order_edit(order_id, parse_fill(lines), yes=yes))

    @mcp.tool()
    def history(orders: int = 16) -> dict[str, Any]:
        return _wrap(lambda: order_service.history(orders))

    @mcp.tool()
    def cart_show() -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            profile = require_profile()
            return public_cart(fetch_cart(require_session(), profile.warehouse))

        return _wrap(_run)

    @mcp.tool()
    def cart_add(product_id: str, qty: int = 1, yes: bool = False) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            _need_yes(yes)
            profile = require_profile()
            cart = put_lines(require_session(), profile.warehouse, [(product_id, qty)])
            return public_cart(cart)

        return _wrap(_run)

    @mcp.tool()
    def cart_fill(lines: str, replace: bool = False, yes: bool = False) -> dict[str, Any]:
        """lines: 'product_id qty' per row. replace=true makes the cart exactly this list."""

        def _run() -> dict[str, Any]:
            _need_yes(yes)
            profile = require_profile()
            session = require_session()
            rows = parse_fill(lines)
            if replace:
                wanted: list[tuple[str, int | float]] = [(p, q) for p, q in rows if q > 0]
                return public_cart(replace_cart(session, profile.warehouse, wanted))
            return public_cart(put_lines(session, profile.warehouse, rows))

        return _wrap(_run)

    return mcp
