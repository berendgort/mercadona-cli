"""One writer for profile.json and session.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

from merca.core.paths import merca_home, profile_path, session_path
from merca.models.profile import Profile, Session

__all__ = (
    "load_profile",
    "load_session",
    "save_profile",
    "save_session",
)


def _ensure_home() -> None:
    home = merca_home()
    home.mkdir(parents=True, exist_ok=True)
    os.chmod(home, 0o700)


def load_profile() -> Profile | None:
    path = profile_path()
    if not path.is_file():
        return None
    return Profile.model_validate_json(path.read_text(encoding="utf-8"))


def save_profile(profile: Profile) -> None:
    _ensure_home()
    profile_path().write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )


def load_session() -> Session | None:
    path = session_path()
    if not path.is_file():
        return None
    return Session.model_validate_json(path.read_text(encoding="utf-8"))


def _write_private(path: Path, text: str) -> None:
    """Create the file at mode 0600. A later chmod would leave a window."""
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
    os.replace(tmp, path)


def save_session(session: Session) -> None:
    _ensure_home()
    payload = json.dumps({"token": session.token, "uuid": session.uuid}, indent=2) + "\n"
    _write_private(session_path(), payload)
