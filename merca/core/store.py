"""One writer for profile.json and session.json."""

from __future__ import annotations

import json
import os
import tempfile
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


def _atomic_write(path: Path, text: str) -> None:
    """Write via a unique 0600 temp file, then replace the destination."""
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def save_profile(profile: Profile) -> None:
    _ensure_home()
    text = json.dumps(profile.model_dump(mode="json"), indent=2) + "\n"
    _atomic_write(profile_path(), text)


def load_session() -> Session | None:
    path = session_path()
    if not path.is_file():
        return None
    return Session.model_validate_json(path.read_text(encoding="utf-8"))


def save_session(session: Session) -> None:
    _ensure_home()
    payload = json.dumps({"token": session.token, "uuid": session.uuid}, indent=2) + "\n"
    _atomic_write(session_path(), payload)
