from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MissionSessionRow(Base):
    __tablename__ = "mission_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mission_key: Mapped[str] = mapped_column(String(128), nullable=False)
    mission_id: Mapped[str] = mapped_column(String(128), nullable=False)
    mission_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    position_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class ObservationRow(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint("session_id", "local_id", name="uq_observation_session_local_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("mission_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    local_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SurfaceMessageRow(Base):
    __tablename__ = "surface_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "local_id", name="uq_surface_message_session_local_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("mission_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    local_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SurfaceReplyRow(Base):
    __tablename__ = "surface_replies"
    __table_args__ = (
        UniqueConstraint("session_id", "local_id", name="uq_surface_reply_session_local_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("mission_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    local_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class MissionEventRow(Base):
    __tablename__ = "mission_events"
    __table_args__ = (
        UniqueConstraint("session_id", "local_id", name="uq_event_session_local_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("mission_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    local_id: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
