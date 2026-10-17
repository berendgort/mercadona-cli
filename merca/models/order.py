"""Order rows and the editable cart of a confirmed order. No address, phone, or payment fields."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("OrderCart", "OrderLine", "OrderSummary")


class OrderSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    status: str
    start: str
    end: str
    products_eur: str
    total_eur: str
    products_count: int


class OrderLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    line_id: int
    product_id: str
    quantity: float
    display_name: str
    unit_price: float
    sources: tuple[str, ...] = ()


class OrderCart(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: str
    cart_id: str
    version: int | None = None
    lines: tuple[OrderLine, ...]
