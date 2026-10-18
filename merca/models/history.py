"""Per-product purchase stats built from delivered orders."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("History", "ProductStat")


class ProductStat(BaseModel):
    model_config = ConfigDict(frozen=True)

    product_id: str
    display_name: str
    orders: int
    share: float
    total_qty: float
    qty_per_order: float
    qty_per_week: float
    first_day: str
    last_day: str
    gap_days: float | None
    unit_price: float


class History(BaseModel):
    model_config = ConfigDict(frozen=True)

    orders_used: int
    first_day: str
    last_day: str
    span_days: int
    products: tuple[ProductStat, ...]
