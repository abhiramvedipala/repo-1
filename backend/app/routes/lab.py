import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app import docker_manager as dm
from app.db import get_db
from app.deps import get_current_user
from app.models import LabSession, User

router = APIRouter(prefix="/api/lab", tags=["lab"])


class StartLabRequest(BaseModel):
    minutes: int | None = None


def _session_out(sess: LabSession) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = sess.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    remaining = max(0, int((expires_at - now).total_seconds()))
    return {
        "status": sess.status,
        "sessionToken": sess.session_token,
        "proxyUrl": f"/proxy/{sess.session_token}/",
        "startedAt": sess.started_at.isoformat() if sess.started_at else None,
        "expiresAt": expires_at.isoformat(),
        "remainingSeconds": remaining,
    }


@router.get("/status")
def lab_status(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()
    if sess is None:
        return {"status": "none"}

    if sess.status == "running" and not dm.container_running(sess.container_id):
        sess.status = "stopped"
        db.commit()

    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = sess.expires_at if sess.expires_at.tzinfo else sess.expires_at.replace(tzinfo=datetime.timezone.utc)
    if sess.status == "running" and expires_at < now:
        dm.stop_container(user.id)
        sess.status = "expired"
        db.commit()

    return _session_out(sess)


@router.post("/start")
def start_lab(body: StartLabRequest, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    minutes = dm.clamp_minutes(body.minutes)
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(minutes=minutes)

    try:
        result = dm.start_container(user.id, minutes)
    except dm.LabError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))

    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()
    if sess is None:
        sess = LabSession(
            user_id=user.id,
            session_token=dm.new_session_token(),
            container_name=f"lab-session-{user.id}",
        )
        db.add(sess)

    sess.container_id = result["container_id"]
    sess.container_ip = result["container_ip"]
    sess.status = "running"
    if not result.get("reused"):
        sess.started_at = now
        sess.expires_at = expires_at
        sess.session_token = dm.new_session_token()
    elif not sess.expires_at:
        sess.expires_at = expires_at
    db.commit()

    return _session_out(sess)


@router.post("/stop")
def stop_lab(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    dm.stop_container(user.id)
    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()
    if sess is not None:
        sess.status = "stopped"
        db.commit()
    return {"status": "stopped"}
