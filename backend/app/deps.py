import datetime

from fastapi import Depends, HTTPException, Request, WebSocket, status
from sqlalchemy.orm import Session as DbSession

from app.config import SESSION_COOKIE_NAME
from app.db import SessionLocal, get_db
from app.models import Session as SessionModel, User


def resolve_session_user(token: str | None, db: DbSession) -> User | None:
    """Shared session-cookie -> User lookup, used by both HTTP and WS auth."""
    if not token:
        return None

    sess = db.get(SessionModel, token)
    if sess is None:
        return None

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = sess.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    if expires_at < now:
        db.delete(sess)
        db.commit()
        return None

    return db.get(User, sess.user_id)


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    user = resolve_session_user(token, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    return user


def get_current_user_ws(websocket: WebSocket) -> User | None:
    """Same cookie-session lookup as get_current_user, for WS endpoints
    (which open their own short-lived DB session rather than using the
    per-request Depends(get_db)). Returns None instead of raising —
    callers close the socket themselves with an appropriate code."""
    token = websocket.cookies.get(SESSION_COOKIE_NAME)
    db = SessionLocal()
    try:
        return resolve_session_user(token, db)
    finally:
        db.close()
