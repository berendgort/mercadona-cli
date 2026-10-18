"""Human tables for the non --json path. Agents read JSON; this is for eyes only."""

from __future__ import annotations

from typing import Any

from rich.table import Table

from merca.cli.console import console

__all__ = ("render",)

_COLUMNS: dict[str, tuple[tuple[str, str], ...]] = {
    "lines": (
        ("product_id", "id"),
        ("display_name", "product"),
        ("quantity", "qty"),
        ("prepared", "packed"),
        ("unit_price", "€/u"),
    ),
    "changed": (("display_name", "product"), ("from", "from"), ("to", "to")),
    "products": (
        ("display_name", "product"),
        ("orders", "orders"),
        ("qty_per_week", "qty/wk"),
        ("gap_days", "every (d)"),
        ("last_day", "last"),
    ),
    "slots": (("date", "date"), ("day", "day"), ("local", "time"), ("available", "free")),
    "orders": (
        ("id", "order"),
        ("status", "status"),
        ("start", "slot (UTC)"),
        ("products_count", "lines"),
        ("total_eur", "total €"),
    ),
}
_FOOTER = (
    "spend",
    "spend_before",
    "spend_after",
    "item_count",
    "count",
    "changes_until",
    "status",
    "sent",
    "matches_plan",
    "orders_used",
    "span_days",
)


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _table(rows: list[dict[str, Any]], key: str) -> Table:
    cols = [(field, title) for field, title in _COLUMNS[key] if any(field in r for r in rows)]
    table = Table(show_header=True, header_style="bold")
    for _field, title in cols:
        table.add_column(title, overflow="fold")
    for row in rows:
        table.add_row(*(_cell(row.get(field)) for field, _title in cols))
    return table


def render(data: Any) -> None:
    if not isinstance(data, dict):
        console.print(data)
        return
    shown = False
    for key in _COLUMNS:
        rows = data.get(key)
        if isinstance(rows, list) and rows and all(isinstance(r, dict) for r in rows):
            console.print(_table(rows, key))
            shown = True
    if not shown:
        console.print(data)
        return
    facts = [f"{k}: {_cell(data[k])}" for k in _FOOTER if k in data]
    if isinstance(data.get("slot"), dict):
        slot = data["slot"]
        facts.append(f"slot: {slot.get('day')} {slot.get('date')} {slot.get('local')}")
    if facts:
        console.print("  ".join(facts))
