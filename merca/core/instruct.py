"""Agent recipe. Stable command list for --json clients."""

from __future__ import annotations

from typing import Any

__all__ = ("instruct_recipe",)


def instruct_recipe() -> dict[str, Any]:
    return {
        "name": "merca",
        "objective": (
            "The right products arrive in a slot the household can receive. "
            "Book the slot early, then trim the order before its deadline."
        ),
        "never": [
            "place an order without --confirm --yes",
            "cancel or delete an order",
            "add or change a payment card",
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
            "merca history --orders 16 --json  # per-product cadence from delivered orders",
            "merca order show <order_id> --json",
            "merca order edit <order_id> --file lines.txt --json  # dry run",
            "merca order edit <order_id> --file lines.txt --yes --json",
            "merca cart --json",
            "merca cart add <id> --qty 1 --yes --json",
            "merca cart fill --file lines.txt --replace --yes --json",
            "merca cart clear --yes --json",
            "merca slots --json",
            "merca checkout --day LUN,MAR,MIE --label 11:00-18:00 --json  # dry run",
            "merca checkout --day LUN,MAR,MIE --label 11:00-18:00 --confirm --yes --json",
        ],
        "writes": (
            "cart add/remove/fill/clear, order edit, and checkout --confirm do nothing "
            "unless --yes is present. Every cart write is re-read and verified."
        ),
        "order_edit": (
            "Sets quantities on a confirmed order before changes_until. Rows are "
            "'product_id qty'; 0 removes; an id not in the order is added. Unlisted lines "
            "stay. Removing every line is refused (that would cancel)."
        ),
        "history": (
            "Learns from what was packed in delivered orders: orders, share, qty_per_week, "
            "gap_days, last_day per product. Delivered orders are cached locally."
        ),
        "ambiguous": "search returns error_type ambiguous and candidates. Pick an id.",
        "auth": (
            "error_type auth includes human_fix. Show login_howto to the human. "
            "Do not invent a token. Do not ask for Cookies."
        ),
        "checkout": (
            "Runs preflight on the live cart and picks the earliest open slot on the given "
            "days inside the local window (--earliest/--latest bound the date). Without "
            "--confirm it stops. With --confirm --yes it places the order with the saved "
            "payment method; refuses if another future order is already booked. "
            "needs_authentication means the human finishes 3-D Secure in the app."
        ),
        "orders": (
            "orders returns id, status, slot, and totals only. "
            "receipt writes a PDF to --out and returns the path. Never print the PDF."
        ),
    }
