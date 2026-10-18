"""Pick the earliest open delivery slot inside the household window. Pure: caller passes now."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from merca.core.exceptions import MercaValidationError
from merca.models.slot import Slot
from merca.policy.slot import check_delivery_slot, normalize_day, parse_slot_time_range

__all__ = ("MADRID", "local_window", "pick_slot")

MADRID = ZoneInfo("Europe/Madrid")
_WEEKDAY = ("LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM")


def _parse(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def local_window(slot: Slot) -> tuple[str, str, str, str]:
    """Day code, local date, local start HH:MM, local end HH:MM."""
    start = _parse(slot.start).astimezone(MADRID)
    end = _parse(slot.end).astimezone(MADRID)
    hours = start.strftime("%H:%M"), end.strftime("%H:%M")
    return _WEEKDAY[start.weekday()], start.date().isoformat(), *hours


def pick_slot(
    slots: Sequence[Slot],
    *,
    days: Sequence[str],
    label: str,
    now: datetime,
    lead_hours: float = 20.0,
    earliest: date | None = None,
    latest: date | None = None,
) -> Slot | None:
    wanted = {normalize_day(day) for day in days}
    for day in wanted:
        ok, errors = check_delivery_slot(day, label)
        if not ok:
            raise MercaValidationError("; ".join(errors))
    lo, hi = parse_slot_time_range(label)
    cutoff = now + timedelta(hours=lead_hours)
    best: Slot | None = None
    for slot in slots:
        if not slot.available:
            continue
        start = _parse(slot.start)
        if start < cutoff:
            continue
        day, _date, local_start, local_end = local_window(slot)
        if day not in wanted or local_start < lo or local_end > hi:
            continue
        local_day = start.astimezone(MADRID).date()
        if earliest is not None and local_day < earliest:
            continue
        if latest is not None and local_day > latest:
            continue
        if best is None or start < _parse(best.start):
            best = slot
    return best
