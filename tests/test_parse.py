"""Parser tests against captured fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from merca.basket.parse import parse_cart
from merca.basket.wire import build_put_body
from merca.catalog.parse import parse_product, parse_search
from merca.catalog.search import resolve_hits
from merca.core.exceptions import MercaAmbiguousError, MercaParseError, MercaValidationError

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"


def _load(name: str) -> dict[str, object]:
    data = json.loads((FIX / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_search_fixture_is_ambiguous() -> None:
    hits = parse_search(_load("search_leche.json"))
    assert len(hits) == 2
    with pytest.raises(MercaAmbiguousError) as caught:
        resolve_hits("leche", hits)
    assert len(caught.value.candidates) == 2


def test_exact_name_picks_one_of_many() -> None:
    hits = parse_search(_load("search_leche.json"))
    chosen = resolve_hits(hits[0].display_name, hits)
    assert chosen.id == hits[0].id


def test_single_hit_resolves() -> None:
    hits = parse_search(_load("search_one.json"))
    assert resolve_hits("leche", hits).id == hits[0].id


def test_product_fixture() -> None:
    product = parse_product(_load("product_17330.json"))
    assert product.id == "17330"
    assert product.unit_price == pytest.approx(1.10)


def test_cart_fixture_spend_comes_from_lines() -> None:
    cart = parse_cart(_load("cart_ok.json"))
    assert len(cart.lines) == 12
    assert cart.lines[0].product_id
    assert cart.lines[0].unit_price > 0


def test_put_body_is_a_full_replacement() -> None:
    body = build_put_body([("10381", 1), ("10379", 2.0)], cart_id="c1", version=4)
    assert body == {
        "id": "c1",
        "version": 4,
        "lines": [
            {"product_id": "10381", "quantity": 1},
            {"product_id": "10379", "quantity": 2},
        ],
    }
    assert build_put_body([], cart_id="c1", version=4)["lines"] == []


def test_put_body_rejects_bad_quantity_and_missing_id() -> None:
    with pytest.raises(MercaValidationError):
        build_put_body([("10381", -1)], cart_id="c1", version=1)
    with pytest.raises(MercaValidationError):
        build_put_body([("10381", 0)], cart_id="c1", version=1)
    with pytest.raises(MercaValidationError):
        build_put_body([("10381", 1)], cart_id="", version=1)


def test_missing_price_is_a_parse_error() -> None:
    with pytest.raises(MercaParseError):
        parse_product({"id": "1", "display_name": "X"})
