"""Slot window and basket bounds."""

from __future__ import annotations

import json
from pathlib import Path

from merca.basket.parse import parse_cart
from merca.models.cart import Cart, CartLine
from merca.models.profile import Profile
from merca.policy.checkout import checkout_plan
from merca.policy.preflight import run_preflight
from merca.policy.slot import check_delivery_slot

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_monday_midday_is_allowed() -> None:
    ok, errors = check_delivery_slot("LUN", "De 11:00 a 13:00")
    assert ok, errors
    ok, errors = check_delivery_slot("Monday", "De 16:00 a 18:00")
    assert ok, errors


def test_friday_and_late_slots_fail() -> None:
    assert check_delivery_slot("VIE", "De 11:00 a 13:00")[0] is False
    assert check_delivery_slot("viernes", "De 11:00 a 13:00")[0] is False
    assert check_delivery_slot("LUN", "De 18:00 a 20:00")[0] is False
    assert check_delivery_slot("LUN", "De 07:00 a 09:00")[0] is False
    assert check_delivery_slot("JUE", "De 11:00 a 13:00")[0] is False


def test_weekly_fixture_passes_preflight() -> None:
    cart = parse_cart(json.loads((FIX / "cart_ok.json").read_text(encoding="utf-8")))
    report = run_preflight(cart, Profile())
    assert report.ok, report.errors
    assert report.item_count == 12
    assert 50 <= report.spend <= 260


def test_blacklist_qty_and_short_cart_fail() -> None:
    line = CartLine(
        product_id="26763",
        quantity=19,
        display_name="merluza",
        unit_price=3.0,
    )
    report = run_preflight(Cart(lines=(line,)), Profile(blacklist=("26763",)))
    assert report.ok is False
    text = " ".join(report.errors)
    assert "Blacklisted" in text
    assert "Quantity" in text
    assert "Item count" in text


def test_checkout_stops_and_rejects_friday() -> None:
    plan = checkout_plan("LUN", "De 11:00 a 13:00")
    assert plan["stopped_before_pay"] is True
    assert "never pays" in plan["human_fix"]
    try:
        checkout_plan("FRI", "De 11:00 a 13:00")
    except Exception as exc:  # noqa: BLE001
        assert "Friday" in str(exc)
    else:
        raise AssertionError("friday checkout should fail")
