"""Turn delivered orders into per-product purchase stats. Pure: no HTTP, no clock."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from merca.core.exceptions import MercaValidationError
from merca.models.history import History, ProductStat
from merca.models.order import DeliveredLine

__all__ = ("DeliveredOrder", "build_history")

DeliveredOrder = tuple[date, Sequence[DeliveredLine]]


def _mean(values: Sequence[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def build_history(orders: Sequence[DeliveredOrder]) -> History:
    """Prepared quantity counts, not ordered: shortages never reached the house."""
    if not orders:
        raise MercaValidationError("no delivered orders to learn from")
    ordered = sorted(orders, key=lambda row: row[0])
    first, last = ordered[0][0], ordered[-1][0]
    # A single order still covers a week of eating.
    span = max((last - first).days, 0) + 7
    weeks = span / 7
    days_by_product: dict[str, list[date]] = {}
    qty: dict[str, float] = {}
    name: dict[str, str] = {}
    price: dict[str, float] = {}
    for day, lines in ordered:
        for line in lines:
            if line.prepared <= 0:
                continue
            pid = line.product_id
            days_by_product.setdefault(pid, [])
            if not days_by_product[pid] or days_by_product[pid][-1] != day:
                days_by_product[pid].append(day)
            qty[pid] = qty.get(pid, 0.0) + line.prepared
            name[pid] = line.display_name
            price[pid] = line.unit_price
    stats: list[ProductStat] = []
    for pid, days in days_by_product.items():
        gaps = [float((b - a).days) for a, b in zip(days, days[1:], strict=False)]
        stats.append(
            ProductStat(
                product_id=pid,
                display_name=name[pid],
                orders=len(days),
                share=round(len(days) / len(ordered), 2),
                total_qty=round(qty[pid], 2),
                qty_per_order=round(qty[pid] / len(days), 2),
                qty_per_week=round(qty[pid] / weeks, 2),
                first_day=days[0].isoformat(),
                last_day=days[-1].isoformat(),
                gap_days=_mean(gaps),
                unit_price=price[pid],
            )
        )
    stats.sort(key=lambda s: (-s.orders, -s.total_qty, s.display_name))
    return History(
        orders_used=len(ordered),
        first_day=first.isoformat(),
        last_day=last.isoformat(),
        span_days=span,
        products=tuple(stats),
    )
