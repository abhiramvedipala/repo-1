import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.config import LAB_MAX_CONCURRENT_SESSIONS
from app.db import get_db
from app.deps import get_current_admin
from app.models import LabSession, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _aware(dt: datetime.datetime | None) -> datetime.datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


@router.get("/stats")
def stats(_admin: object = Depends(get_current_admin), db: DbSession = Depends(get_db)):
    now = datetime.datetime.now(datetime.timezone.utc)

    total_users = db.query(User).count()
    sessions = (
        db.query(LabSession, User.email)
        .join(User, LabSession.user_id == User.id)
        .filter(LabSession.status.in_(["running", "queued"]))
        .order_by(LabSession.status.desc(), LabSession.queued_at.asc(), LabSession.started_at.asc())
        .all()
    )

    running = []
    queued = []
    for sess, email in sessions:
        if sess.status == "running":
            expires_at = _aware(sess.expires_at)
            running.append(
                {
                    "userEmail": email,
                    "containerName": sess.container_name,
                    "startedAt": sess.started_at.isoformat() if sess.started_at else None,
                    "remainingSeconds": max(0, int((expires_at - now).total_seconds())) if expires_at else 0,
                }
            )
        else:
            queued_at = _aware(sess.queued_at)
            queued.append(
                {
                    "userEmail": email,
                    "queuedForSeconds": max(0, int((now - queued_at).total_seconds())) if queued_at else 0,
                    "requestedMinutes": sess.requested_minutes,
                }
            )

    return {
        "totalUsers": total_users,
        "maxConcurrentSessions": LAB_MAX_CONCURRENT_SESSIONS,
        "runningCount": len(running),
        "queuedCount": len(queued),
        "running": running,
        "queued": queued,
    }
