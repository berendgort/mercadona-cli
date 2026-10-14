"""Order list rows. No address, phone, or payment fields."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("OrderSummary",)


class OrderSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    status: str
    start: str
    end: str
    products_eur: str
    total_eur: str
    products_count: int
