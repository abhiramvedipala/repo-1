import asyncio
import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import docker_manager as dm
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD, FRONTEND_ORIGIN, LAB_REAPER_INTERVAL_SECONDS
from app.db import SessionLocal, init_db
from app.models import LabSession, User
from app.routes import auth, files, lab, proxy, tasks, terminal
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

_reaper_task: asyncio.Task | None = None


async def _reap_expired_sessions_forever():
    """Auto-stop + destroy containers whose session has timed out, so a
    forgotten lab doesn't run forever. Runs independently of anyone
    polling GET /api/lab/status."""
    while True:
        await asyncio.sleep(LAB_REAPER_INTERVAL_SECONDS)
        db = SessionLocal()
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            expired = db.query(LabSession).filter(LabSession.status == "running").all()
            for sess in expired:
                expires_at = sess.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
                if expires_at < now:
                    try:
                        dm.stop_container(sess.user_id)
                    except dm.LabError:
                        pass
                    sess.status = "expired"
            db.commit()
        except Exception as e:
            print(f"[reaper] error: {e}")
        finally:
            db.close()


@app.on_event("startup")
def on_startup():
    global _reaper_task
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL.lower()).first()
        if existing is None:
            admin = User(
                email=ADMIN_EMAIL.lower(),
                password_hash=hash_password(ADMIN_PASSWORD),
                is_admin=1,
            )
            db.add(admin)
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
