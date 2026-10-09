"""Basket policy. Line prices are the only spend figure."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from merca.models.cart import Cart
from merca.models.profile import Profile

__all__ = ("Preflight", "run_preflight")


class Preflight(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    errors: tuple[str, ...]
    item_count: int
    spend: float


def run_preflight(cart: Cart, profile: Profile) -> Preflight:
    errors: list[str] = []
    seen: set[str] = set()
    spend = 0.0
    banned = set(profile.blacklist)
    allowed = set(profile.whitelist)
    for line in cart.lines:
        if line.product_id in seen:
            errors.append(f"Duplicate product {line.product_id}")
        seen.add(line.product_id)
        if line.product_id in banned:
            errors.append(f"Blacklisted product {line.product_id} ({line.display_name})")
        if allowed and line.product_id not in allowed:
            errors.append(f"Product {line.product_id} is not on the whitelist")
        if line.quantity < 1 or line.quantity > profile.qty_max:
            errors.append(
                f"Quantity {line.quantity} for {line.product_id} is outside 1..{profile.qty_max}"
            )
        spend += line.unit_price * line.quantity
    count = len(cart.lines)
    if count < profile.item_min or count > profile.item_max:
        errors.append(
            f"Item count {count} is outside {profile.item_min}..{profile.item_max}"
        )
    if spend < profile.spend_min or spend > profile.spend_max:
        errors.append(
            f"Spend {spend:.2f} is outside {profile.spend_min:.2f}..{profile.spend_max:.2f}"
        )
    return Preflight(
        ok=not errors,
        errors=tuple(errors),
        item_count=count,
        spend=round(spend, 2),
    )
