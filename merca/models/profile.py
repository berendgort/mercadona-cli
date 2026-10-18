"""Local profile and session DTOs. The store in core is the only writer."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ("Profile", "Session")


class Profile(BaseModel):
    model_config = ConfigDict(frozen=True)

    postal_code: str = ""
    warehouse: str = ""
    blacklist: tuple[str, ...] = ()
    whitelist: tuple[str, ...] = ()
    qty_max: int = 18
    spend_min: float = 60.0
    spend_max: float = 260.0
    item_min: int = 10
    item_max: int = 65


class Session(BaseModel):
    model_config = ConfigDict(frozen=True)

    token: str = Field(repr=False)
    uuid: str
