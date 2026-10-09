#!/usr/bin/env python3
"""Korotkevich checks for merca, plus the cart PUT fixture lock."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "merca"
MAX_LOC = 250

LAYER: dict[str, int] = {
    "merca.models": 10,
    "merca.core.exceptions": 15,
    "merca.http": 20,
    "merca.core": 30,
    "merca.catalog": 40,
    "merca.basket": 40,
    "merca.policy": 40,
    "merca.cli": 50,
    "merca.mcp": 50,
}

PRINT_ALLOW = {
    "merca/cli/catch.py",
}


def _pkg_rank(mod: str) -> int | None:
    for prefix, rank in sorted(LAYER.items(), key=lambda item: -len(item[0])):
        if mod == prefix or mod.startswith(prefix + "."):
            return rank
    return None


def check_loc() -> list[str]:
    bad: list[str] = []
    for path in PKG.rglob("*.py"):
        n = len(path.read_text(encoding="utf-8").splitlines())
        if n > MAX_LOC:
            bad.append(f"{path.relative_to(ROOT)}: {n} LOC > {MAX_LOC}")
    return bad


def check_emdash() -> list[str]:
    bad: list[str] = []
    for path in PKG.rglob("*.py"):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "\u2014" in line or "\u2013" in line:
                bad.append(f"{path.relative_to(ROOT)}:{i}: em/en-dash")
    return bad


def check_print() -> list[str]:
    bad: list[str] = []
    for path in PKG.rglob("*.py"):
        rel = str(path.relative_to(ROOT))
        if rel in PRINT_ALLOW:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    bad.append(f"{rel}:{node.lineno}: bare print()")
    return bad


def check_layers() -> list[str]:
    bad: list[str] = []
    for path in PKG.rglob("*.py"):
        parts = path.relative_to(PKG).with_suffix("").parts
        if path.name == "__init__.py":
            mod = ".".join(("merca", *parts[:-1])) if len(parts) > 1 else "merca"
        else:
            mod = ".".join(("merca", *parts))
        src_rank = _pkg_rank(mod)
        if src_rank is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if not name.startswith("merca."):
                    continue
                dst = _pkg_rank(name)
                if dst is not None and dst > src_rank:
                    bad.append(
                        f"{path.relative_to(ROOT)}: {mod} (rank {src_rank}) "
                        f"imports higher {name} (rank {dst})"
                    )
    return bad


def _consts(path: Path) -> dict[str, tuple[str, ...]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Tuple):
            continue
        vals: list[str] = []
        for elt in node.value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                vals.append(elt.value)
        found[target.id] = tuple(vals)
    return found


def check_cart_fixture() -> list[str]:
    wire = _consts(ROOT / "merca" / "basket" / "wire.py")
    required = wire.get("REQUIRED_PUT_LINE_KEYS")
    forbidden = wire.get("FORBIDDEN_PUT_KEYS")
    if not required or not forbidden:
        return ["basket/wire.py missing PUT key tuples"]
    meta = json.loads((ROOT / "fixtures" / "cart_put_request.json").read_text(encoding="utf-8"))
    bad: list[str] = []
    if tuple(meta.get("required_line_keys") or ()) != required:
        bad.append("cart fixture required_line_keys != REQUIRED_PUT_LINE_KEYS")
    if tuple(meta.get("forbidden_keys") or ()) != forbidden:
        bad.append("cart fixture forbidden_keys != FORBIDDEN_PUT_KEYS")
    example = meta.get("example") or {}
    line = (example.get("lines") or [{}])[0]
    if tuple(line.keys()) != required:
        bad.append("cart fixture example line keys != REQUIRED_PUT_LINE_KEYS")
    for key in forbidden:
        if key in example or key in line:
            bad.append(f"cart fixture contains forbidden key {key}")
    return bad


def main() -> int:
    bad = check_loc() + check_emdash() + check_print() + check_layers() + check_cart_fixture()
    if bad:
        print("\n".join(bad), file=sys.stderr)
        return 1
    print("code quality ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
