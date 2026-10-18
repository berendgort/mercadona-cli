"""Place an order from the live cart: checkout, delivery info, confirm.

Mirrors the tienda web app. The saved payment method on the account is used as is;
this module never adds or changes a card. A 202 from confirm means the bank wants
3-D Secure: the human finishes it in the app.
"""

from __future__ import annotations

from typing import Any

from merca.core.exceptions import MercaNotFoundError, MercaParseError, MercaValidationError
from merca.http.client import TIENDA, HttpClient
from merca.models.cart import Cart
from merca.models.profile import Session
from merca.models.slot import Slot

__all__ = (
    "build_checkout_body",
    "fetch_address",
    "fetch_slots",
    "parse_slots",
    "place_order",
)


def _base(customer_id: str) -> str:
    return f"{TIENDA}/api/customers/{customer_id}"


def fetch_address(session: Session, *, client: HttpClient | None = None) -> dict[str, Any]:
    """The permanent delivery address as the API returns it. Never printed."""
    http = client or HttpClient(token=session.token)
    payload = http.request("GET", f"{_base(session.uuid)}/addresses/")
    rows = [row for row in payload.get("results") or [] if isinstance(row, dict)]
    if not rows:
        raise MercaNotFoundError("No delivery address on the account")
    rows.sort(key=lambda row: not row.get("permanent_address"))
    return rows[0]


def parse_slots(payload: dict[str, Any]) -> tuple[tuple[Slot, ...], dict[str, dict[str, Any]]]:
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise MercaParseError("slots response has no results list")
    slots: list[Slot] = []
    raw_by_id: dict[str, dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict) or raw.get("id") is None:
            continue
        slot = Slot(
            id=str(raw["id"]),
            start=str(raw.get("start") or ""),
            end=str(raw.get("end") or ""),
            available=bool(raw.get("available")) and raw.get("open") is not False,
            price=str(raw.get("price") or ""),
        )
        slots.append(slot)
        raw_by_id[slot.id] = raw
    return tuple(slots), raw_by_id


def fetch_slots(
    session: Session, address_id: str, *, client: HttpClient | None = None
) -> tuple[tuple[Slot, ...], dict[str, dict[str, Any]]]:
    http = client or HttpClient(token=session.token)
    payload = http.request("GET", f"{_base(session.uuid)}/addresses/{address_id}/slots/")
    return parse_slots(payload)


def build_checkout_body(cart: Cart) -> dict[str, Any]:
    """Web shape: {"cart": {id, version?, lines: [{quantity, product_id, sources}]}}."""
    if not cart.cart_id:
        raise MercaValidationError("cart has no id; reload it with merca cart --json")
    if not cart.lines:
        raise MercaValidationError("cart is empty")
    lines = [
        {"quantity": line.quantity, "product_id": line.product_id, "sources": list(line.sources)}
        for line in cart.lines
    ]
    inner: dict[str, Any] = {"id": cart.cart_id, "lines": lines}
    if cart.version:
        inner["version"] = cart.version
    return {"cart": inner}


def place_order(
    session: Session,
    cart: Cart,
    address: dict[str, Any],
    slot: dict[str, Any],
    *,
    client: HttpClient | None = None,
) -> dict[str, Any]:
    """Returns order_id on success, or needs_authentication with the checkout id."""
    http = client or HttpClient(token=session.token)
    base = f"{_base(session.uuid)}/checkouts"
    created = http.request("POST", f"{base}/", body=build_checkout_body(cart))
    checkout_id = created.get("id")
    if checkout_id is None:
        raise MercaParseError("checkout create returned no id")
    url = f"{base}/{checkout_id}/"
    http.request("PUT", url + "delivery-info/", body={"address": address, "slot": slot})
    current = http.request("GET", url)
    if not current.get("payment_method"):
        raise MercaValidationError(
            "No saved payment method on the checkout. Finish this order in the Mercadona app"
        )
    summary = current.get("summary") if isinstance(current.get("summary"), dict) else {}
    confirmed = http.request("POST", url + "confirm/")
    order_id = confirmed.get("order_id")
    result: dict[str, Any] = {
        "checkout_id": str(checkout_id),
        "slot_id": str(slot.get("id")),
        "total_eur": str((summary or {}).get("total") or ""),
    }
    if order_id is not None:
        return {**result, "order_id": str(order_id), "confirmed": True}
    return {
        **result,
        "confirmed": False,
        "needs_authentication": True,
        "human_fix": "The bank asked for 3-D Secure. Open the Mercadona app and finish checkout.",
    }
