"""Typer entry. Agents pass --json."""

from __future__ import annotations

import typer

from merca.cli import cmd_cart, cmd_catalog, cmd_ops, cmd_policy

__all__ = ("app", "cli")

app = typer.Typer(
    name="merca",
    help=(
        "Mercadona cart for humans and agents. "
        "Search, check the Monday window, stop before pay. "
        "Recipe: merca instruct --json."
    ),
    no_args_is_help=True,
    add_completion=False,
)

cmd_ops.register(app)
cmd_catalog.register(app)
app.add_typer(cmd_cart.cart_app, name="cart")
cmd_policy.register(app)


def cli() -> None:
    app()


if __name__ == "__main__":
    cli()
