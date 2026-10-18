"""One delivery slot. Times are ISO UTC as the API sends them."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ("Slot",)


class Slot(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    start: str
    end: str
    available: bool
    price: str = ""
