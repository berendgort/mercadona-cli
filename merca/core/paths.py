"""Config directory. Session file is mode 0600. No network."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ("merca_home", "profile_path", "session_path")


def merca_home() -> Path:
    override = os.environ.get("MERCA_HOME")
    if override:
        return Path(override)
    return Path.home() / ".config" / "merca"


def profile_path() -> Path:
    return merca_home() / "profile.json"


def session_path() -> Path:
    return merca_home() / "session.json"
