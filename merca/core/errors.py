"""Map exceptions to error_type and retryable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from merca.core.exceptions import (
    MercaAmbiguousError,
    MercaAuthError,
    MercaError,
    MercaHTTPError,
    MercaNotFoundError,
    MercaParseError,
    MercaRateLimitError,
    MercaUnsupportedError,
    MercaValidationError,
)

__all__ = (
    "ErrorClassification",
    "classify_error",
)


@dataclass(frozen=True)
class ErrorClassification:
    error_type: str
    retryable: bool
    http_status: int | None = None
    retry_after_s: float | None = None

    def as_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "error_type": self.error_type,
            "retryable": self.retryable,
        }
        if self.http_status is not None:
            fields["http_status"] = self.http_status
        if self.retry_after_s is not None:
            fields["retry_after_s"] = self.retry_after_s
        return fields


def classify_error(exc: BaseException) -> ErrorClassification:
    if isinstance(exc, MercaAmbiguousError):
        return ErrorClassification("ambiguous", retryable=False)
    if isinstance(exc, MercaAuthError):
        return ErrorClassification("auth", retryable=False)
    if isinstance(exc, MercaValidationError):
        return ErrorClassification("validation_error", retryable=False)
    if isinstance(exc, MercaUnsupportedError):
        return ErrorClassification("unsupported", retryable=False)
    if isinstance(exc, MercaNotFoundError):
        return ErrorClassification("not_found", retryable=False)
    if isinstance(exc, MercaParseError):
        return ErrorClassification("parse_error", retryable=False)
    if isinstance(exc, MercaRateLimitError):
        return ErrorClassification(
            "rate_limited",
            retryable=True,
            http_status=exc.status_code,
            retry_after_s=exc.retry_after_s,
        )
    if isinstance(exc, MercaHTTPError):
        status = exc.status_code
        retryable = status is not None and (status == 429 or status >= 500)
        return ErrorClassification("http_error", retryable=retryable, http_status=status)
    if isinstance(exc, MercaError):
        return ErrorClassification("error", retryable=False)
    return ErrorClassification("error", retryable=False)
