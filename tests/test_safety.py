"""The package must not grow a pay button or a browser driver."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "merca"
BANNED = (
    "playwright",
    "9224",
    "/confirmation/",
    "payment-method",
    "USER_MERCADONA",
    "dienke",
    "allesaangort",
    "Marina 277",
)


def test_package_has_no_pay_or_browser_path() -> None:
    for path in PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in BANNED:
            assert token.lower() not in text, f"{path.name} contains {token}"


def test_checkout_module_does_not_import_http() -> None:
    tree = ast.parse((PKG / "policy" / "checkout.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("merca.http")
            assert "basket" not in node.module
