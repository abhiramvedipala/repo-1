import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from app import docker_manager as dm
from app.config import LAB_MAX_CONCURRENT_SESSIONS
from app.db import get_db
from app.deps import get_current_user
from app.models import LabSession, User

router = APIRouter(prefix="/api/lab", tags=["lab"])


class StartLabRequest(BaseModel):
    minutes: int | None = None


def _aware(dt: datetime.datetime | None) -> datetime.datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def _running_count(db: DbSession) -> int:
    return db.query(LabSession).filter(LabSession.status == "running").count()


def _queue_position(db: DbSession, sess: LabSession) -> int:
    """1-based position among queued sessions, oldest first."""
    ahead = (
        db.query(LabSession)
        .filter(LabSession.status == "queued", LabSession.queued_at < sess.queued_at)
        .count()
    )
    return ahead + 1


def _session_out(sess: LabSession, db: DbSession) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    out = {
        "status": sess.status,
        "sessionToken": sess.session_token,
        "proxyUrl": f"/proxy/{sess.session_token}/",
    }
    if sess.status == "queued":
        out["queuePosition"] = _queue_position(db, sess)
        out["queueLength"] = db.query(LabSession).filter(LabSession.status == "queued").count()
        return out

    expires_at = _aware(sess.expires_at)
    out["startedAt"] = sess.started_at.isoformat() if sess.started_at else None
    out["expiresAt"] = expires_at.isoformat() if expires_at else None
    out["remainingSeconds"] = max(0, int((expires_at - now).total_seconds())) if expires_at else 0
    return out


@router.get("/status")
def lab_status(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()
    if sess is None:
        return {"status": "none"}

    if sess.status == "running" and not dm.container_running(sess.container_id):
        sess.status = "stopped"
        db.commit()

    expires_at = _aware(sess.expires_at)
    now = datetime.datetime.now(datetime.timezone.utc)
    if sess.status == "running" and expires_at and expires_at < now:
        dm.stop_container(user.id)
        sess.status = "expired"
        db.commit()

    return _session_out(sess, db)


@router.post("/start")
def start_lab(body: StartLabRequest, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    minutes = dm.clamp_minutes(body.minutes)

    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()

    # Already running or already queued: idempotent, just report current state.
    if sess is not None and sess.status == "running" and dm.container_running(sess.container_id):
        return _session_out(sess, db)
    if sess is not None and sess.status == "queued":
        return _session_out(sess, db)

    if sess is None:
        sess = LabSession(user_id=user.id, session_token=dm.new_session_token(), container_name="")
        db.add(sess)

    # Global concurrency cap: past it, queue instead of starting.
    if _running_count(db) >= LAB_MAX_CONCURRENT_SESSIONS:
        sess.status = "queued"
        sess.queued_at = datetime.datetime.now(datetime.timezone.utc)
        sess.requested_minutes = minutes
        sess.container_id = None
        sess.container_ip = None
        sess.started_at = None
        sess.expires_at = None
        db.commit()
        return _session_out(sess, db)

    try:
        result = dm.start_container(user.id, minutes)
    except dm.LabError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))

    now = datetime.datetime.now(datetime.timezone.utc)
    sess.container_id = result["container_id"]
    sess.container_ip = result["container_ip"]
    sess.container_name = f"lab-session-{user.id}"
    sess.status = "running"
    sess.queued_at = None
    if not result.get("reused"):
        sess.started_at = now
        sess.expires_at = now + datetime.timedelta(minutes=minutes)
        sess.session_token = dm.new_session_token()
    elif not sess.expires_at:
        sess.expires_at = now + datetime.timedelta(minutes=minutes)
    db.commit()

    return _session_out(sess, db)


@router.post("/stop")
def stop_lab(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    dm.stop_container(user.id)
    sess = db.query(LabSession).filter(LabSession.user_id == user.id).first()
    if sess is not None:
        sess.status = "stopped"
        sess.queued_at = None
        db.commit()
    return {"status": "stopped"}
