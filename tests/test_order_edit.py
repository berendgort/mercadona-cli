"""Order edit: full-list PUT, deadline, no cancel, no new products, no token."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from merca.basket.order_edit import (
    build_order_put_body,
    parse_edit_window,
    parse_order_cart,
    plan_order_edit,
    put_order_cart,
)
from merca.core.exceptions import MercaNotFoundError, MercaValidationError
from merca.http.client import HttpClient
from merca.models.profile import Session
from merca.policy.order_view import order_diff

ROOT = Path(__file__).resolve().parents[1]
BEFORE = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)


def _load(name: str) -> dict[str, Any]:
    data = json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _cart() -> Any:
    return parse_order_cart("1001", _load("order_cart.json"))


def _window() -> Any:
    return parse_edit_window(_load("order_detail.json"))


def test_window_keeps_only_status_and_deadline() -> None:
    status, until = _window()
    assert status == "confirmed"
    assert until == datetime(2026, 10, 18, 17, 59, 59, tzinfo=timezone.utc)


def test_plan_sets_quantities_and_removes_zero() -> None:
    after = plan_order_edit(_cart(), [("82765", 2), ("35343", 0)], window=_window(), now=BEFORE)
    qty = {line.product_id: line.quantity for line in after.lines}
    assert qty == {"3819": 8.0, "82765": 2.0}
    diff = order_diff(_cart(), after)
    assert diff["lines_before"] == 3
    assert diff["lines_after"] == 2
    assert diff["spend_after"] < diff["spend_before"]


def test_put_body_is_full_list_in_web_shape() -> None:
    after = plan_order_edit(_cart(), [("35343", 0)], window=_window(), now=BEFORE)
    body = build_order_put_body(after)
    assert set(body) == {"cart"}
    assert body["cart"]["id"] == "00000000-0000-4000-8000-000000000001"
    assert "version" not in body["cart"]
    for line in body["cart"]["lines"]:
        assert set(line) == {"id", "quantity", "product_id", "sources"}
        assert isinstance(line["quantity"], int)
    assert [line["product_id"] for line in body["cart"]["lines"]] == ["3819", "82765"]


def test_refuses_after_deadline() -> None:
    late = datetime(2026, 10, 18, 18, 0, tzinfo=timezone.utc)
    with pytest.raises(MercaValidationError, match="deadline"):
        plan_order_edit(_cart(), [("35343", 0)], window=_window(), now=late)


def test_refuses_non_confirmed_order() -> None:
    _status, until = _window()
    with pytest.raises(MercaValidationError, match="confirmed"):
        plan_order_edit(_cart(), [("35343", 0)], window=("delivered", until), now=BEFORE)


def test_refuses_removing_every_line() -> None:
    zero = [(line.product_id, 0) for line in _cart().lines]
    with pytest.raises(MercaValidationError, match="cancels"):
        plan_order_edit(_cart(), zero, window=_window(), now=BEFORE)


def test_refuses_new_product_and_duplicates() -> None:
    with pytest.raises(MercaNotFoundError):
        plan_order_edit(_cart(), [("99999", 1)], window=_window(), now=BEFORE)
    with pytest.raises(MercaValidationError, match="twice"):
        plan_order_edit(_cart(), [("3819", 1), ("3819", 2)], window=_window(), now=BEFORE)


def test_put_hits_order_cart_path_with_put_and_hides_token() -> None:
    seen: dict[str, Any] = {}

    def transport(method: str, url: str, **kwargs: Any) -> tuple[int, str]:
        seen.update(method=method, url=url, body=kwargs["body"], headers=kwargs["headers"])
        return 200, "{}"

    client = HttpClient(token="SECRET-TOKEN", transport=transport)
    session = Session(token="SECRET-TOKEN", uuid="user-uuid")
    after = plan_order_edit(_cart(), [("35343", 0)], window=_window(), now=BEFORE)
    put_order_cart(session, "3087", after, client=client)
    assert seen["method"] == "PUT"
    assert seen["url"].endswith("/customers/user-uuid/orders/1001/cart/")
    assert "SECRET-TOKEN" not in json.dumps(seen["body"])


def test_order_id_must_be_digits() -> None:
    bad = _cart().model_copy(update={"order_id": "../1"})
    with pytest.raises(MercaValidationError):
        put_order_cart(Session(token="t", uuid="u"), "3087", bad, client=HttpClient(token="t"))


def test_new_product_is_appended_without_line_id() -> None:
    from merca.models.product import Product

    milk = Product(id="10933", display_name="Leche", slug="leche", unit_price=1.15, share_url="")
    after = plan_order_edit(
        _cart(), [("10933", 3)], window=_window(), now=BEFORE, new_products={"10933": milk}
    )
    body = build_order_put_body(after)
    added = body["cart"]["lines"][-1]
    assert added == {"quantity": 3, "product_id": "10933", "sources": ["+SA"]}
    assert all("id" in line for line in body["cart"]["lines"][:-1])
    assert order_diff(_cart(), after)["changed"] == [
        {"product_id": "10933", "display_name": "Leche", "from": 0.0, "to": 3.0}
    ]
