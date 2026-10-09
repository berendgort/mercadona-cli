#!/usr/bin/env python3
"""Run the flow matrix against the real merca binary. One row, one JSON result."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/merca-dogfood")


def _merca(home: Path, args: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env["MERCA_HOME"] = str(home)
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-m", "merca.cli.main", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "error_type": "parse_error",
            "error": result.stdout,
            "stderr": result.stderr,
        }
    if not isinstance(payload, dict):
        payload = {"ok": False, "error_type": "parse_error", "error": "stdout was not an object"}
    payload["_exit"] = result.returncode
    return payload


def _slot(day: str, label: str) -> list[str]:
    return ["slot", "--day", day, "--label", label, "--json"]


def _checkout(day: str, label: str) -> list[str]:
    return ["checkout", "--day", day, "--label", label, "--json"]


def main() -> int:
    home = OUT / "home"
    home.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, list[str], str]] = [
        ("instruct", ["instruct", "--json"], "ok"),
        ("doctor", ["doctor", "--json"], "ok"),
        ("setup", ["setup", "--cp", "08860", "--wh", "3087", "--json"], "ok"),
        ("slot_friday", _slot("VIE", "De 11:00 a 13:00"), "validation_error"),
        ("slot_monday", _slot("LUN", "De 11:00 a 13:00"), "ok"),
        ("slot_late", _slot("LUN", "De 18:00 a 20:00"), "validation_error"),
        ("cart_add_no_yes", ["cart", "add", "10381", "--qty", "1", "--json"], "validation_error"),
        ("cart_no_session", ["cart", "--json"], "auth"),
        ("checkout_stop", _checkout("LUN", "De 11:00 a 13:00"), "stop"),
        ("checkout_friday", _checkout("FRI", "De 11:00 a 13:00"), "validation_error"),
        (
            "preflight",
            ["preflight", "--fixture", str(ROOT / "fixtures" / "cart_ok.json"), "--json"],
            "ok",
        ),
        ("search_leche", ["search", "leche", "--json"], "ambiguous"),
    ]
    failed = 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, args, expect in rows:
        payload = _merca(home, args)
        (OUT / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        data = payload.get("data")
        if expect == "ok":
            good = payload.get("ok") is True
        elif expect == "stop":
            good = (
                payload.get("ok") is True
                and isinstance(data, dict)
                and data.get("stopped_before_pay") is True
            )
        else:
            good = payload.get("error_type") == expect
        mark = "ok" if good else "FAIL"
        print(f"{mark} {name} exit={payload.get('_exit')} type={payload.get('error_type')}")
        failed += 0 if good else 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
