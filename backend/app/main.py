import asyncio
import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import docker_manager as dm
from app.config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    FRONTEND_ORIGIN,
    LAB_MAX_CONCURRENT_SESSIONS,
    LAB_REAPER_INTERVAL_SECONDS,
)
from app.db import SessionLocal, init_db
from app.models import LabSession, User
from app.routes import admin, auth, files, lab, proxy, tasks, terminal
from app.security import hash_password

app = FastAPI(title="Lab Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(files.router)
app.include_router(terminal.router)
app.include_router(lab.router)
app.include_router(proxy.router)
app.include_router(admin.router)

_reaper_task: asyncio.Task | None = None


def _aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


async def _reap_expired_sessions_forever():
    """Auto-stop + destroy containers whose session has timed out (so a
    forgotten lab doesn't run forever), then promote the oldest queued
    session into any slot that frees up. Runs independently of anyone
    polling GET /api/lab/status."""
    while True:
        await asyncio.sleep(LAB_REAPER_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            running = db.query(LabSession).filter(LabSession.status == "running").all()
            for sess in running:
                expires_at = _aware(sess.expires_at)
                if expires_at and expires_at < now:
                    try:
                        dm.stop_container(sess.user_id)
                    except dm.LabError:
                        pass
                    sess.status = "expired"
            db.commit()

            free_slots = LAB_MAX_CONCURRENT_SESSIONS - _running_count(db)
            if free_slots > 0:
                queued = (
                    db.query(LabSession)
                    .filter(LabSession.status == "queued")
                    .order_by(LabSession.queued_at.asc())
                    .limit(free_slots)
                    .all()
                )
                for sess in queued:
                    _promote_queued(db, sess)
        except Exception as e:
            print(f"[reaper] error: {e}")
        finally:
            db.close()


def _running_count(db) -> int:
    return db.query(LabSession).filter(LabSession.status == "running").count()


def _promote_queued(db, sess: LabSession) -> None:
    minutes = sess.requested_minutes or None
    try:
        result = dm.start_container(sess.user_id, minutes)
    except dm.LabError as e:
        # leave it queued — it'll be retried next tick rather than lost
        print(f"[reaper] failed to promote user {sess.user_id}: {e}")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    sess.container_id = result["container_id"]
    sess.container_ip = result["container_ip"]
    sess.container_name = f"lab-session-{sess.user_id}"
    sess.status = "running"
    sess.queued_at = None
    sess.started_at = now
    sess.expires_at = now + datetime.timedelta(minutes=dm.clamp_minutes(minutes))
    db.commit()


@app.on_event("startup")
def on_startup():
    global _reaper_task
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL.lower()).first()
        if existing is None:
            admin_user = User(
                email=ADMIN_EMAIL.lower(),
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=1,
            )
            db.add(admin_user)
            db.commit()
            print(f"[seed] created admin user: {ADMIN_EMAIL}")
    finally:
        db.close()

    _reaper_task = asyncio.create_task(_reap_expired_sessions_forever())


@app.on_event("shutdown")
def on_shutdown():
    if _reaper_task is not None:
        _reaper_task.cancel()


@app.get("/api/health")
def health():
    return {"ok": True}
