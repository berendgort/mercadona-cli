"""Agent recipe. Stable command list for --json clients."""

from __future__ import annotations

from typing import Any

__all__ = ("instruct_recipe",)


def instruct_recipe() -> dict[str, Any]:
    return {
        "name": "merca",
        "objective": "Put the right products in the Mercadona cart. The human pays in the app.",
        "never": [
            "confirm an order",
            "pay",
            "print the session token",
            "send a password",
        ],
        "setup": "merca setup --cp 08860 --wh 3087 --json",
        "login": "merca login --token <MO-user.token> --uuid <MO-user.uuid> --json",
        "flows": [
            "merca search leche --json",
            "merca product <id> --json",
            "merca cart --json",
            "merca cart add <id> --qty 1 --yes --json",
            "merca slot --day LUN --label 'De 11:00 a 13:00' --json",
            "merca preflight --fixture cart.json --json",
            "merca checkout --day LUN --label 'De 11:00 a 13:00' --fixture cart.json --json",
        ],
        "writes": "cart add and cart remove do nothing unless --yes is present.",
        "ambiguous": "search returns error_type ambiguous and candidates. Pick an id.",
        "auth": "error_type auth includes human_fix. Ask the human to paste the token.",
        "checkout": "Prints the slot and stops. There is no pay command.",
    }
