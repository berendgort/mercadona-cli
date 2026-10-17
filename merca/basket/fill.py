"""Parse a 'product_id qty' file. Shared by cart fill and order edit."""

from __future__ import annotations

from merca.core.exceptions import MercaValidationError

__all__ = ("parse_fill",)


def parse_fill(text: str) -> list[tuple[str, int]]:
    parsed: list[tuple[str, int]] = []
    for raw in text.splitlines():
        row = raw.split("#", 1)[0].strip()
        if not row:
            continue
        parts = row.split()
        if len(parts) != 2 or not parts[1].isdigit():
            raise MercaValidationError(f"expected 'product_id qty', got {raw!r}")
        parsed.append((parts[0], int(parts[1])))
    if not parsed:
        raise MercaValidationError("fill file has no lines")
    return parsed
