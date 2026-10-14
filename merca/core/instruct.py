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
        "login": "merca login --token '<token>' --uuid '<uuid>' --json",
        "login_howto": {
            "need": ["MO-user.token", "MO-user.uuid"],
            "where": (
                "tienda.mercadona.es (logged in) → F12 → Application → "
                "Local Storage → https://tienda.mercadona.es → key MO-user"
            ),
            "not_cookies": [
                "__mo_ca",
                "__mo_da",
                "__mo_ui",
                "_abck",
                "bm_sz",
                "amplitude_*",
                "g_state",
            ],
            "note": (
                "Cookies panel is wrong. Local Storage key MO-user is a JSON object; "
                "copy the token and uuid string fields only. Run login in your own "
                "terminal so the token never hits chat."
            ),
            "command": "merca login --token '<token>' --uuid '<uuid>' --json",
            "verify": "merca doctor --json  # session: true, session_mode_ok: true",
        },
        "flows": [
            "merca search leche --json",
            "merca product <id> --json",
            "merca orders --limit 8 --json",
            "merca receipt <order_id> --out ticket.pdf --json",
            "merca cart --json",
            "merca cart add <id> --qty 1 --yes --json",
            "merca cart fill --file lines.txt --yes --json",
            "merca slot --day LUN --label 'De 11:00 a 13:00' --json",
            "merca preflight --json",
            "merca checkout --day LUN --label 'De 11:00 a 13:00' --json",
        ],
        "writes": "cart add and cart remove do nothing unless --yes is present.",
        "ambiguous": "search returns error_type ambiguous and candidates. Pick an id.",
        "auth": (
            "error_type auth includes human_fix. Show login_howto to the human. "
            "Do not invent a token. Do not ask for Cookies."
        ),
        "checkout": (
            "Loads the live cart when a session exists, runs preflight, prints the slot, "
            "and stops. There is no pay command. --fixture skips the live cart."
        ),
        "orders": (
            "orders returns id, status, slot, and totals only. "
            "receipt writes a PDF to --out and returns the path. Never print the PDF."
        ),
    }
