"""Live catalog search. Opt in with pytest -m live."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.live
def test_live_search_leche_is_ambiguous(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["MERCA_HOME"] = str(tmp_path)
    env["PYTHONPATH"] = str(ROOT)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "merca.cli.main",
            "setup",
            "--cp",
            "08860",
            "--wh",
            "3087",
            "--json",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "-m", "merca.cli.main", "search", "leche", "--json"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["error_type"] == "ambiguous"
    assert payload["candidates"]
