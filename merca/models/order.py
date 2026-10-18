"""Order rows, delivered lines, and the editable cart of a confirmed order.

No address, phone, or payment fields.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("DeliveredLine", "OrderCart", "OrderLine", "OrderSummary")


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
    """One line of a confirmed order. line_id 0 means a product new to the order."""

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


class DeliveredLine(BaseModel):
    """What the warehouse actually packed. prepared < ordered means a shortage."""

    model_config = ConfigDict(frozen=True)

    product_id: str
    display_name: str
    ordered: float
    prepared: float
    unit_price: float
    total_eur: float
