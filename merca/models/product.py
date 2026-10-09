"""Catalog product."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("Product",)


class Product(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    display_name: str
    slug: str
    unit_price: float
    share_url: str
    brand: str = ""
