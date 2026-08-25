from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ADMIN_EMAIL, ADMIN_PASSWORD, FRONTEND_ORIGIN
from app.db import SessionLocal, init_db
from app.models import User
from app.routes import auth, files, tasks
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


@app.on_event("startup")
def on_startup():
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


@app.get("/api/health")
def health():
    return {"ok": True}
