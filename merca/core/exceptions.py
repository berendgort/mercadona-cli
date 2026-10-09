"""Shared errors. Importable by http and core."""

from __future__ import annotations

from typing import Any

__all__ = (
    "MercaAmbiguousError",
    "MercaAuthError",
    "MercaError",
    "MercaHTTPError",
    "MercaNotFoundError",
    "MercaParseError",
    "MercaRateLimitError",
    "MercaUnsupportedError",
    "MercaValidationError",
)


class MercaError(Exception):
    """Base."""


class MercaHTTPError(MercaError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MercaRateLimitError(MercaHTTPError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        retry_after_s: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code)
        self.retry_after_s = retry_after_s


class MercaAuthError(MercaError):
    """Missing or rejected session."""


class MercaParseError(MercaError):
    pass


class MercaNotFoundError(MercaError):
    pass


class MercaUnsupportedError(MercaError):
    """Wire shape not captured yet."""


class MercaValidationError(MercaError):
    """Caller input or basket policy failed. Nothing was sent."""


class MercaAmbiguousError(MercaError):
    """More than one product matched. Caller must pick an id."""

    def __init__(self, message: str, *, candidates: list[Any]) -> None:
        super().__init__(message)
        self.candidates = candidates
