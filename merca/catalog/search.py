"""Public catalog search. Ambiguous queries return candidates, not a guess."""

from __future__ import annotations

from merca.catalog.parse import parse_product, parse_search
from merca.core.exceptions import MercaAmbiguousError, MercaNotFoundError
from merca.http.client import SEARCH_URL, TIENDA, HttpClient
from merca.models.product import Product

__all__ = ("get_product", "resolve_hits", "search_products")

_CANDIDATES = 8


def resolve_hits(query: str, hits: list[Product]) -> Product:
    if not hits:
        raise MercaNotFoundError(f"No product for {query!r}")
    needle = query.casefold()
    exact = [hit for hit in hits if hit.display_name.casefold() == needle]
    if len(exact) == 1:
        return exact[0]
    if len(hits) == 1 and not exact:
        return hits[0]
    shown = exact or hits
    raise MercaAmbiguousError(
        f"{len(shown)} products match {query!r}. Pass a product id.",
        candidates=shown[:_CANDIDATES],
    )


def search_products(query: str, warehouse: str, *, client: HttpClient | None = None) -> Product:
    http = client or HttpClient()
    payload = http.request(
        "GET",
        SEARCH_URL,
        params={"q": query, "wh": warehouse, "lang": "es"},
    )
    return resolve_hits(query, parse_search(payload))


def get_product(product_id: str, warehouse: str, *, client: HttpClient | None = None) -> Product:
    http = client or HttpClient()
    payload = http.request(
        "GET",
        f"{TIENDA}/api/products/{product_id}/",
        params={"lang": "es", "wh": warehouse},
    )
    return parse_product(payload)
