import re

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from app.config import COOKIE_SECURE, SESSION_COOKIE_NAME, SESSION_TTL_SECONDS
from app.db import get_db
from app.deps import get_current_user
from app.models import Session as SessionModel, User
from app.schemas import LoginRequest, SignupRequest, UserOut
from app.security import hash_password, new_session_token, session_expiry, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _start_session(user: User, response: Response, db: DbSession) -> UserOut:
    token = new_session_token()
    db.add(SessionModel(token=token, user_id=user.id, expires_at=session_expiry()))
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return UserOut(id=user.id, email=user.email, is_admin=bool(user.is_admin))


@router.post("/signup", response_model=UserOut)
def signup(body: SignupRequest, response: Response, db: DbSession = Depends(get_db)):
    email = body.email.lower().strip()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "enter a valid email address")
    if len(body.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "password must be at least 8 characters")
    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "an account with that email already exists")

    user = User(email=email, password_hash=hash_password(body.password), is_admin=0)
    db.add(user)
    db.commit()
    db.refresh(user)

    return _start_session(user, response, db)


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid email or password")

    return _start_session(user, response, db)


@router.post("/logout")
def logout(response: Response, request_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    # deps already validated the session exists; just drop the cookie + row
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    db.query(SessionModel).filter(SessionModel.user_id == request_user.id).delete()
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email, is_admin=bool(user.is_admin))
