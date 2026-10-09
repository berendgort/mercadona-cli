"""Load profile and session or fail closed. No HTTP."""

from __future__ import annotations

from merca.core.exceptions import MercaAuthError, MercaValidationError
from merca.core.store import load_profile, load_session
from merca.models.profile import Profile, Session

__all__ = ("require_profile", "require_session")


def require_profile() -> Profile:
    profile = load_profile()
    if profile is None or not profile.warehouse or not profile.postal_code:
        raise MercaValidationError("Run merca setup --cp <postal> --wh <warehouse> --json")
    return profile


def require_session() -> Session:
    session = load_session()
    if session is None or not session.token or not session.uuid:
        raise MercaAuthError("No session saved")
    return session
