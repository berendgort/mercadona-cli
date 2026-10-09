"""Real CLI subprocess. No live Mercadona calls."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(home: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["MERCA_HOME"] = str(home)
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "merca.cli.main", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _json(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def test_instruct_and_doctor(tmp_path: Path) -> None:
    payload = _json(_run(tmp_path, "instruct", "--json"))
    assert payload["ok"] is True
    data = payload["data"]
    assert isinstance(data, dict)
    assert data["never"]
    doctor = _json(_run(tmp_path, "doctor", "--json"))
    assert doctor["ok"] is True
    assert isinstance(doctor["data"], dict)
    assert doctor["data"]["pays"] is False


def test_setup_login_does_not_echo_the_token(tmp_path: Path) -> None:
    setup = _json(_run(tmp_path, "setup", "--cp", "08860", "--wh", "3087", "--json"))
    assert setup["ok"] is True
    secret = "session-token-do-not-print"
    login = _run(tmp_path, "login", "--token", secret, "--uuid", "user-uuid", "--json")
    assert secret not in login.stdout
    assert secret not in login.stderr
    payload = _json(login)
    assert payload["ok"] is True
    mode = (tmp_path / "session.json").stat().st_mode
    assert stat.S_IMODE(mode) == 0o600
    assert list(tmp_path.glob(".session.json.*")) == []
    doctor = _json(_run(tmp_path, "doctor", "--json"))
    assert isinstance(doctor["data"], dict)
    assert doctor["data"]["session_mode_ok"] is True
    assert secret not in json.dumps(doctor)


def test_cart_add_without_yes_does_not_need_a_session(tmp_path: Path) -> None:
    result = _run(tmp_path, "cart", "add", "10381", "--qty", "1", "--json")
    payload = _json(result)
    assert result.returncode == 1
    assert payload["error_type"] == "validation_error"
    assert not (tmp_path / "session.json").exists()


def test_cart_without_session_is_auth(tmp_path: Path) -> None:
    _run(tmp_path, "setup", "--cp", "08860", "--wh", "3087", "--json")
    payload = _json(_run(tmp_path, "cart", "--json"))
    assert payload["error_type"] == "auth"
    assert "human_fix" in payload
    fix = str(payload["human_fix"])
    assert "--token" in fix
    assert "--password" not in fix


def test_slot_and_checkout_stop_before_pay(tmp_path: Path) -> None:
    bad = _json(_run(tmp_path, "slot", "--day", "VIE", "--label", "De 11:00 a 13:00", "--json"))
    assert bad["error_type"] == "validation_error"
    good = _json(_run(tmp_path, "slot", "--day", "LUN", "--label", "De 11:00 a 13:00", "--json"))
    assert good["ok"] is True
    late = _json(_run(tmp_path, "slot", "--day", "LUN", "--label", "De 18:00 a 20:00", "--json"))
    assert late["ok"] is False
    checkout = _json(
        _run(
            tmp_path,
            "checkout",
            "--day",
            "LUN",
            "--label",
            "De 11:00 a 13:00",
            "--json",
        )
    )
    assert checkout["ok"] is True
    assert isinstance(checkout["data"], dict)
    assert checkout["data"]["stopped_before_pay"] is True
    friday = _json(
        _run(tmp_path, "checkout", "--day", "FRI", "--label", "De 11:00 a 13:00", "--json")
    )
    assert friday["error_type"] == "validation_error"
    assert "stopped_before_pay" not in friday


def test_preflight_fixture(tmp_path: Path) -> None:
    fixture = ROOT / "fixtures" / "cart_ok.json"
    payload = _json(_run(tmp_path, "preflight", "--fixture", str(fixture), "--json"))
    assert payload["ok"] is True
    checked = _json(
        _run(
            tmp_path,
            "checkout",
            "--day",
            "LUN",
            "--label",
            "De 11:00 a 13:00",
            "--fixture",
            str(fixture),
            "--json",
        )
    )
    assert checked["ok"] is True
    assert isinstance(checked["data"], dict)
    assert checked["data"]["cart_checked"] is True
