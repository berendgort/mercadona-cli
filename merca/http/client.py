"""curl_cffi client. Errors never include the bearer token."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from merca.core.exceptions import (
    MercaAuthError,
    MercaHTTPError,
    MercaNotFoundError,
    MercaParseError,
    MercaRateLimitError,
)

__all__ = ("SEARCH_URL", "TIENDA", "HttpClient")

TIENDA = "https://tienda.mercadona.es"
SEARCH_URL = "https://tornillos.mercadona.es/search"
_MIN_INTERVAL_S = 0.3

Transport = Callable[..., tuple[int, str]]
BytesTransport = Callable[..., tuple[int, bytes]]


def _curl(
    method: str,
    url: str,
    *,
    params: dict[str, str] | None,
    body: dict[str, Any] | None,
    headers: dict[str, str],
) -> tuple[int, str]:
    from curl_cffi import requests

    fn = {"GET": requests.get, "PUT": requests.put, "POST": requests.post}[method]
    response = fn(
        url,
        params=params,
        json=body,
        headers=headers,
        impersonate="chrome",
        timeout=30,
    )
    return response.status_code, response.text


def _curl_bytes(
    method: str,
    url: str,
    *,
    params: dict[str, str] | None,
    body: dict[str, Any] | None,
    headers: dict[str, str],
) -> tuple[int, bytes]:
    from curl_cffi import requests

    fn = {"GET": requests.get, "PUT": requests.put, "POST": requests.post}[method]
    response = fn(
        url,
        params=params,
        json=body,
        headers=headers,
        impersonate="chrome",
        timeout=30,
    )
    return response.status_code, response.content


def _decode(status: int, text: str) -> dict[str, Any]:
    if status == 401:
        raise MercaAuthError("Session rejected")
    if status == 429:
        raise MercaRateLimitError("Rate limited", status_code=429)
    if status >= 400:
        raise MercaHTTPError(f"HTTP {status}", status_code=status)
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MercaParseError("Response was not JSON") from exc
    if not isinstance(data, dict):
        raise MercaParseError("Response was not an object")
    return data


class HttpClient:
    """Polite JSON client. Pass a transport in tests."""

    def __init__(
        self,
        *,
        token: str | None = None,
        transport: Transport | None = None,
        bytes_transport: BytesTransport | None = None,
    ) -> None:
        self._token = token
        self._transport = transport or _curl
        self._bytes_transport = bytes_transport or _curl_bytes
        self._last = 0.0

    def __repr__(self) -> str:
        return "HttpClient()"

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._transport is _curl:
            wait = _MIN_INTERVAL_S - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
        try:
            status, text = self._transport(method, url, params=params, body=body, headers=headers)
        except MercaHTTPError:
            raise
        except Exception:
            # Transport errors can echo Authorization. Keep the message generic.
            raise MercaHTTPError("HTTP request failed") from None
        finally:
            if self._transport is _curl:
                self._last = time.monotonic()
        return _decode(status, text)

    def request_bytes(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        accept: str = "application/pdf",
    ) -> tuple[int, bytes]:
        """Binary GET. Errors never include the bearer token."""
        headers = {"Accept": accept}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._pace()
        try:
            status, data = self._bytes_transport(
                method, url, params=params, body=None, headers=headers
            )
        except MercaHTTPError:
            raise
        except Exception:
            raise MercaHTTPError("HTTP request failed") from None
        finally:
            self._mark()
        if status == 401:
            raise MercaAuthError("Session rejected")
        if status == 404:
            raise MercaNotFoundError("Not found")
        if status == 429:
            raise MercaRateLimitError("Rate limited", status_code=429)
        if status >= 400:
            raise MercaHTTPError(f"HTTP {status}", status_code=status)
        return status, data

    def _pace(self) -> None:
        if self._bytes_transport is not _curl_bytes:
            return
        wait = _MIN_INTERVAL_S - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)

    def _mark(self) -> None:
        if self._bytes_transport is _curl_bytes:
            self._last = time.monotonic()
