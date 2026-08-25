import datetime
import secrets

import bcrypt

from app.config import SESSION_TTL_SECONDS


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=SESSION_TTL_SECONDS
    )
