"""HTTP errors must not echo the bearer token."""

from __future__ import annotations

import pytest

from merca.core.exceptions import MercaAuthError, MercaHTTPError
from merca.http.client import HttpClient


def test_transport_crash_hides_the_token() -> None:
    def boom(*_args: object, **_kwargs: object) -> tuple[int, str]:
        raise RuntimeError("Bearer SECRET-TOKEN")

    client = HttpClient(token="SECRET-TOKEN", transport=boom)
    with pytest.raises(MercaHTTPError) as caught:
        client.request("GET", "https://tienda.mercadona.es/api/products/1/")
    assert "SECRET-TOKEN" not in str(caught.value)
    assert "HttpClient()" == repr(client)


def test_401_is_auth() -> None:
    def unauthorized(*_args: object, **_kwargs: object) -> tuple[int, str]:
        return 401, '{"detail":"Bearer SECRET-TOKEN"}'

    client = HttpClient(token="SECRET-TOKEN", transport=unauthorized)
    with pytest.raises(MercaAuthError) as caught:
        client.request("GET", "https://tienda.mercadona.es/api/customers/u/cart/")
    assert "SECRET-TOKEN" not in str(caught.value)
