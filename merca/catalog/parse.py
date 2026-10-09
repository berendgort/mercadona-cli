"""Parse captured catalog JSON. Fixtures are the source of truth."""

from __future__ import annotations

from typing import Any

from merca.core.exceptions import MercaParseError
from merca.models.product import Product

__all__ = ("parse_product", "parse_search")


def _price(raw: dict[str, Any]) -> float:
    block = raw.get("price_instructions")
    if not isinstance(block, dict) or block.get("unit_price") is None:
        raise MercaParseError(f"product {raw.get('id')} missing unit_price")
    try:
        return float(block["unit_price"])
    except (TypeError, ValueError) as exc:
        raise MercaParseError(f"product {raw.get('id')} has a bad unit_price") from exc


def parse_product(raw: dict[str, Any]) -> Product:
    if not isinstance(raw, dict):
        raise MercaParseError("product is not an object")
    if raw.get("id") is None or not raw.get("display_name"):
        raise MercaParseError("product missing id or display_name")
    return Product(
        id=str(raw["id"]),
        display_name=str(raw["display_name"]),
        slug=str(raw.get("slug") or ""),
        unit_price=_price(raw),
        share_url=str(raw.get("share_url") or ""),
        brand=str(raw.get("brand") or ""),
    )


def parse_search(payload: dict[str, Any]) -> list[Product]:
    hits = payload.get("hits")
    if not isinstance(hits, list):
        raise MercaParseError("search payload missing hits")
    return [parse_product(hit) for hit in hits]
