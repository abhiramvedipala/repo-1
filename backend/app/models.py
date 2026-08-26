import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Integer, nullable=False, default=0)  # 0/1, sqlite/pg friendly bool
    created_at = Column(DateTime(timezone=True), default=utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("TaskProgress", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="sessions")


class LabSession(Base):
    """A lab session for a user: queued, running, or finished.

    One row per user (a new "start" reuses or replaces it) — containers are
    namespaced by user_id throughout (workspace dir, container name), so
    this scales to many concurrent users as-is; Phase 4 adds the piece that
    was still single-tenant: a global concurrency cap with a wait queue
    when every slot is taken (see LAB_MAX_CONCURRENT_SESSIONS).
    """

    __tablename__ = "lab_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    session_token = Column(String, unique=True, nullable=False, index=True)
    container_name = Column(String, nullable=False)
    container_id = Column(String, nullable=True)
    # No published host port: the container sits on an `internal: true`
    # Docker network (no egress), and the backend reaches it directly by
    # its address on that bridge instead — see docker_manager.py.
    container_ip = Column(String, nullable=True)
    container_port = Column(Integer, nullable=False, default=8080)
    status = Column(String, nullable=False, default="starting")  # queued|starting|running|stopped|expired
    # Set when queued, so the queue can be served oldest-first.
    queued_at = Column(DateTime(timezone=True), nullable=True)
    # The session length the user asked for; applied once a queued session
    # is actually promoted and its container starts (started_at/expires_at
    # only mean something from that point on).
    requested_minutes = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class TaskProgress(Base):
    __tablename__ = "task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_user_task"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="not_started")  # not_started|current|passed
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="progress")
