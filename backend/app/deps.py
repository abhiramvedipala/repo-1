import datetime

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.config import SESSION_COOKIE_NAME
from app.db import get_db
from app.models import Session as SessionModel, User


def get_current_user(request: Request, db: DbSession = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")

    sess = db.get(SessionModel, token)
    if sess is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid session")

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = sess.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    if expires_at < now:
        db.delete(sess)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session expired")

    user = db.get(User, sess.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user
