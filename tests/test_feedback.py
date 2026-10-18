"""History learning, slot picking, verified cart writes, checkout body. Offline."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from merca.basket.cart import apply_changes, replace_cart
from merca.basket.checkout_live import build_checkout_body, parse_slots, place_order
from merca.basket.delivered import parse_delivered_lines
from merca.basket.parse import parse_cart
from merca.core.exceptions import MercaHTTPError, MercaValidationError
from merca.http.client import HttpClient
from merca.models.cart import Cart, CartLine
from merca.models.order import DeliveredLine
from merca.models.profile import Session
from merca.policy.history import build_history
from merca.policy.slot_pick import pick_slot

FIX = Path(__file__).resolve().parents[1] / "fixtures"
SESSION = Session(token="SECRET-TOKEN", uuid="u")


def _load(name: str) -> dict[str, Any]:
    data = json.loads((FIX / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _line(pid: str, qty: float, prepared: float | None = None) -> DeliveredLine:
    done = qty if prepared is None else prepared
    return DeliveredLine(
        product_id=pid, display_name=pid, ordered=qty, prepared=done, unit_price=1.0, total_eur=done
    )


def test_delivered_lines_keep_prepared_and_drop_the_rest() -> None:
    lines = parse_delivered_lines(_load("delivered_lines.json"))
    assert len(lines) == 3
    assert lines[2].prepared == 0.0 and lines[2].ordered == 1.0
    assert set(lines[0].model_dump()) == {
        "product_id",
        "display_name",
        "ordered",
        "prepared",
        "unit_price",
        "total_eur",
    }


def test_history_counts_prepared_quantity_and_cadence() -> None:
    orders = [
        (date(2026, 10, 1), [_line("milk", 6), _line("kiwi", 3, prepared=0)]),
        (date(2026, 10, 8), [_line("milk", 4), _line("kiwi", 2)]),
        (date(2026, 10, 15), [_line("milk", 2), _line("milk", 2)]),
    ]
    history = build_history(orders)
    by_id = {row.product_id: row for row in history.products}
    assert history.orders_used == 3
    assert history.span_days == 21
    assert by_id["milk"].orders == 3
    assert by_id["milk"].total_qty == 14
    assert by_id["milk"].qty_per_week == pytest.approx(14 / 3, abs=0.01)
    assert by_id["milk"].gap_days == 7.0
    assert by_id["kiwi"].orders == 1  # the shortage never reached the house
    assert history.products[0].product_id == "milk"


def test_history_needs_orders() -> None:
    with pytest.raises(MercaValidationError):
        build_history([])


def test_pick_slot_respects_window_days_lead_and_dates() -> None:
    slots, _raw = parse_slots(_load("slots.json"))
    now = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)
    days = ["LUN", "MAR", "MIE"]
    first = pick_slot(slots, days=days, label="11:00-18:00", now=now)
    # Slot 1 is 09:00 local, slot 2 is full, slot 4 is Friday.
    assert first is not None and first.id == "3"
    later = pick_slot(slots, days=days, label="11:00-18:00", now=now, earliest=date(2026, 10, 21))
    assert later is not None and later.id == "5"
    assert (
        pick_slot(slots, days=days, label="11:00-18:00", now=now, latest=date(2026, 10, 19)) is None
    )
    with pytest.raises(MercaValidationError):
        pick_slot(slots, days=["VIE"], label="11:00-18:00", now=now)


def test_apply_changes_sets_absolute_and_zero_removes() -> None:
    cart = Cart(
        lines=(
            CartLine(product_id="a", quantity=2, display_name="a", unit_price=1.0),
            CartLine(product_id="b", quantity=1, display_name="b", unit_price=1.0),
        ),
        cart_id="c",
        version=3,
    )
    assert apply_changes(cart, [("a", 0), ("b", 4), ("c", 1)]) == [("b", 4), ("c", 1)]


class FakeCart:
    """Server that ignores stale versions, like the real one."""

    def __init__(self, sticky: bool = True) -> None:
        self.lines: list[dict[str, Any]] = []
        self.version = 1
        self.sticky = sticky
        self.bodies: list[dict[str, Any]] = []

    def __call__(self, method: str, url: str, **kw: Any) -> tuple[int, str]:
        if method == "PUT":
            body = kw["body"]
            self.bodies.append(body)
            if self.sticky and body.get("version") == self.version:
                self.lines = body["lines"]
                self.version += 1
            return 200, "{}"
        rows = [
            {
                "product_id": row["product_id"],
                "quantity": row["quantity"],
                "product": {
                    "display_name": row["product_id"],
                    "price_instructions": {"unit_price": "1"},
                },
            }
            for row in self.lines
        ]
        return 200, json.dumps({"id": "cart-1", "version": self.version, "lines": rows})


def test_replace_cart_sends_id_and_version_and_verifies() -> None:
    server = FakeCart()
    client = HttpClient(token="SECRET-TOKEN", transport=server)
    cart = replace_cart(SESSION, "3087", [("a", 2), ("b", 1)], client=client)
    assert [(line.product_id, line.quantity) for line in cart.lines] == [("a", 2), ("b", 1)]
    assert server.bodies[0]["id"] == "cart-1" and server.bodies[0]["version"] == 1
    assert "SECRET-TOKEN" not in json.dumps(server.bodies)


def test_replace_cart_fails_loud_when_the_write_does_not_stick() -> None:
    client = HttpClient(token="t", transport=FakeCart(sticky=False))
    with pytest.raises(MercaHTTPError):
        replace_cart(SESSION, "3087", [("a", 1)], client=client)


def test_checkout_body_is_the_web_shape() -> None:
    cart = parse_cart(_load("cart_ok.json")).model_copy(update={"cart_id": "cart-1", "version": 7})
    body = build_checkout_body(cart)
    assert set(body) == {"cart"}
    assert body["cart"]["id"] == "cart-1" and body["cart"]["version"] == 7
    assert set(body["cart"]["lines"][0]) == {"quantity", "product_id", "sources"}
    with pytest.raises(MercaValidationError):
        build_checkout_body(cart.model_copy(update={"cart_id": ""}))


def _checkout_server(confirm: dict[str, Any], payment: bool = True) -> Any:
    calls: list[tuple[str, str]] = []

    def transport(method: str, url: str, **kw: Any) -> tuple[int, str]:
        calls.append((method, url.split("/checkouts")[-1]))
        if method == "POST" and url.endswith("/checkouts/"):
            return 201, json.dumps({"id": 55})
        if url.endswith("/confirm/"):
            return 201, json.dumps(confirm)
        if method == "GET":
            body = {"payment_method": {"id": 1} if payment else None, "summary": {"total": "70.00"}}
            return 200, json.dumps(body)
        return 204, ""

    return transport, calls


def test_place_order_runs_create_delivery_check_confirm() -> None:
    cart = parse_cart(_load("cart_ok.json")).model_copy(update={"cart_id": "cart-1"})
    transport, calls = _checkout_server({"order_id": 999})
    client = HttpClient(token="t", transport=transport)
    out = place_order(SESSION, cart, {"id": 1}, {"id": "3"}, client=client)
    assert out["confirmed"] is True and out["order_id"] == "999"
    assert [c[0] for c in calls] == ["POST", "PUT", "GET", "POST"]
    assert calls[1][1].endswith("/delivery-info/")


def test_place_order_reports_3ds_and_refuses_without_card() -> None:
    cart = parse_cart(_load("cart_ok.json")).model_copy(update={"cart_id": "cart-1"})
    transport, _calls = _checkout_server({"authentication_uuid": "x"})
    out = place_order(
        SESSION, cart, {"id": 1}, {"id": "3"}, client=HttpClient(token="t", transport=transport)
    )
    assert out["confirmed"] is False and out["needs_authentication"] is True
    transport, calls = _checkout_server({"order_id": 1}, payment=False)
    with pytest.raises(MercaValidationError):
        place_order(
            SESSION, cart, {"id": 1}, {"id": "3"}, client=HttpClient(token="t", transport=transport)
        )
    assert not any(url.endswith("/confirm/") for _m, url in calls)
