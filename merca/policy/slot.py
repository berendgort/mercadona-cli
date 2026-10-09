"""Delivery window. Monday through Wednesday, 11:00 to 18:00. Never Friday."""

from __future__ import annotations

import re

__all__ = (
    "DELIVERY_WINDOW_MAX",
    "DELIVERY_WINDOW_MIN",
    "check_delivery_slot",
    "parse_slot_time_range",
)

DELIVERY_WINDOW_MIN = "10:59"
DELIVERY_WINDOW_MAX = "18:01"

_DAYS = {
    "LUN": "LUN",
    "LUNES": "LUN",
    "MON": "LUN",
    "MONDAY": "LUN",
    "MAR": "MAR",
    "MARTES": "MAR",
    "TUE": "MAR",
    "TUESDAY": "MAR",
    "MIE": "MIE",
    "MIERCOLES": "MIE",
    "WED": "MIE",
    "WEDNESDAY": "MIE",
    "VIE": "VIE",
    "VIERNES": "VIE",
    "FRI": "VIE",
    "FRIDAY": "VIE",
}
_ALLOWED = frozenset({"LUN", "MAR", "MIE"})


def _norm_day(day: str) -> str:
    text = day.strip().upper().replace("É", "E").replace("Á", "A")
    return _DAYS.get(text, text)


def parse_slot_time_range(slot_label: str) -> tuple[str, str]:
    matches = re.findall(r"(\d{1,2}:\d{2})", slot_label)
    if len(matches) >= 2:
        return matches[0].zfill(5), matches[1].zfill(5)
    raise ValueError(f"Could not parse hours from slot label: {slot_label}")


def check_delivery_slot(slot_day: str, slot_label: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    day = _norm_day(slot_day)
    if day == "VIE":
        errors.append(f"Forbidden delivery day '{slot_day}' (never Friday).")
    elif day not in _ALLOWED:
        errors.append(f"Delivery day '{slot_day}' is outside Monday, Tuesday, Wednesday.")
    try:
        start_time, end_time = parse_slot_time_range(slot_label)
    except ValueError as exc:
        errors.append(str(exc))
        return False, errors
    if start_time < DELIVERY_WINDOW_MIN:
        errors.append(
            f"Time window start {start_time} is earlier than {DELIVERY_WINDOW_MIN}."
        )
    if end_time > DELIVERY_WINDOW_MAX:
        errors.append(f"Time window end {end_time} is later than {DELIVERY_WINDOW_MAX}.")
    return (not errors, errors)
