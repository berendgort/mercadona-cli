"""Search and product lookup."""

from __future__ import annotations

from typing import Any

import typer

from merca.catalog.search import get_product, search_products
from merca.cli.catch import run_cmd
from merca.core.access import require_profile

__all__ = ("register",)


def _search(
    query: str = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        profile = require_profile()
        product = search_products(query, profile.warehouse)
        return product.model_dump(mode="json")

    run_cmd(_run, as_json=json_out)


def _product(
    product_id: str = typer.Argument(...),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    def _run() -> dict[str, Any]:
        profile = require_profile()
        return get_product(product_id, profile.warehouse).model_dump(mode="json")

    run_cmd(_run, as_json=json_out)


def register(app: typer.Typer) -> None:
    app.command("search")(_search)
    app.command("product")(_product)
