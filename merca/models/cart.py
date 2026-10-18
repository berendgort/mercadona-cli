"""Basket lines. Prices on the line are the spend source."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("Cart", "CartLine")


class CartLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: str
    quantity: int
    display_name: str
    unit_price: float
    slug: str = ""
    sources: tuple[str, ...] = ()


class Cart(BaseModel):
    model_config = ConfigDict(frozen=True)

    lines: tuple[CartLine, ...]
    cart_id: str = ""
    version: int | None = None
    products_count: int = 0
