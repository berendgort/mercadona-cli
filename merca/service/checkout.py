"""Slot listing and checkout. An order is placed only when confirm and yes are both true."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from merca.basket.cart import fetch_cart
from merca.basket.checkout_live import fetch_address, fetch_slots, place_order
from merca.basket.orders import list_orders
from merca.core.access import require_profile, require_session
from merca.core.exceptions import MercaNotFoundError, MercaValidationError
from merca.core.store import load_profile
from merca.models.profile import Profile, Session
from merca.models.slot import Slot
from merca.policy.preflight import run_preflight
from merca.policy.slot_pick import local_window, pick_slot

__all__ = ("checkout", "slots", "upcoming_orders")


def _slot_view(slot: Slot) -> dict[str, Any]:
    day, local_date, start, end = local_window(slot)
    return {
        "id": slot.id,
        "day": day,
        "date": local_date,
        "local": f"{start}-{end}",
        "price": slot.price,
    }


def slots() -> dict[str, Any]:
    session = require_session()
    address = fetch_address(session)
    found, _raw = fetch_slots(session, str(address["id"]))
    rows = [{**_slot_view(slot), "available": slot.available} for slot in found]
    return {"slots": rows, "available": sum(1 for row in rows if row["available"])}


def upcoming_orders(session: Session, warehouse: str, now: datetime) -> list[str]:
    return [
        row.id
        for row in list_orders(session, warehouse)
        if row.status == "confirmed"
        and datetime.fromisoformat(row.start.replace("Z", "+00:00")) > now
    ]


def checkout(
    days: list[str],
    label: str,
    *,
    earliest: date | None = None,
    latest: date | None = None,
    lead_hours: float = 20.0,
    confirm: bool = False,
    yes: bool = False,
    allow_second: bool = False,
) -> dict[str, Any]:
    if not days:
        raise MercaValidationError("need at least one delivery day")
    if confirm and not yes:
        raise MercaValidationError("Refusing to place an order without --yes")
    profile = require_profile()
    session = require_session()
    cart = fetch_cart(session, profile.warehouse)
    report = run_preflight(cart, load_profile() or Profile())
    if not report.ok:
        raise MercaValidationError("; ".join(report.errors))
    now = datetime.now(timezone.utc)
    address = fetch_address(session)
    found, raw = fetch_slots(session, str(address["id"]))
    slot = pick_slot(
        found,
        days=days,
        label=label,
        now=now,
        lead_hours=lead_hours,
        earliest=earliest,
        latest=latest,
    )
    if slot is None:
        raise MercaNotFoundError("No open slot inside the window and dates")
    base = {"preflight": report.model_dump(mode="json"), "slot": _slot_view(slot)}
    if not confirm:
        return {**base, "stopped_before_pay": True, "confirmed": False}
    pending = upcoming_orders(session, profile.warehouse, now)
    if pending and not allow_second:
        raise MercaValidationError(
            f"Order {', '.join(pending)} is already booked. Edit it with merca order edit, "
            "or pass --allow-second"
        )
    return {
        **base,
        **place_order(session, cart, address, raw[slot.id]),
        "stopped_before_pay": False,
    }
