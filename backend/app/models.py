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


class TaskProgress(Base):
    __tablename__ = "task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id", name="uq_user_task"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="not_started")  # not_started|current|passed
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="progress")
