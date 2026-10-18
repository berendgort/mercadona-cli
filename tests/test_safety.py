"""The package must not grow a cancel button, a card path, or a browser driver."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "merca"
BANNED = (
    "playwright",
    "9224",
    "/confirmation/",
    "/cancel/",
    "payment-method",
    "payment-cards",
    "payment-methods",
    "authentication/",
    '"DELETE"',
    "USER_MERCADONA",
    "dienke",
    "allesaangort",
    "Marina 277",
)


def test_package_has_no_cancel_card_or_browser_path() -> None:
    for path in PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in BANNED:
            assert token.lower() not in text, f"{path.name} contains {token}"


def test_order_confirm_lives_in_one_module() -> None:
    hits = [p.name for p in PKG.rglob("*.py") if "confirm/" in p.read_text(encoding="utf-8")]
    assert hits == ["checkout_live.py"]


def test_service_refuses_confirm_without_yes() -> None:
    import pytest

    from merca.core.exceptions import MercaValidationError
    from merca.service.checkout import checkout

    with pytest.raises(MercaValidationError, match="--yes"):
        checkout(["LUN"], "11:00-18:00", confirm=True, yes=False)


def test_checkout_module_does_not_import_http() -> None:
    tree = ast.parse((PKG / "policy" / "checkout.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("merca.http")
            assert "basket" not in node.module
