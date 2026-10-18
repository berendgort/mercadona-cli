"""Offline checkout plan (fixture or no session). This module does not call HTTP."""

from __future__ import annotations

from typing import Any

from merca.core.exceptions import MercaValidationError
from merca.models.cart import Cart
from merca.models.profile import Profile
from merca.policy.preflight import run_preflight
from merca.policy.slot import check_delivery_slot

__all__ = ("PAY_IN_APP", "checkout_plan")

PAY_IN_APP = (
    "Stopped before the order. Book it with checkout --confirm --yes, or in the Mercadona app."
)


def checkout_plan(
    day: str,
    label: str,
    *,
    cart: Cart | None = None,
    profile: Profile | None = None,
) -> dict[str, Any]:
    ok, errors = check_delivery_slot(day, label)
    if not ok:
        raise MercaValidationError("; ".join(errors))
    payload: dict[str, Any] = {
        "stopped_before_pay": True,
        "day": day,
        "label": label,
        "cart_checked": cart is not None,
        "human_fix": PAY_IN_APP,
    }
    if cart is not None:
        report = run_preflight(cart, profile or Profile())
        if not report.ok:
            raise MercaValidationError("; ".join(report.errors))
        payload["preflight"] = report.model_dump(mode="json")
    return payload
