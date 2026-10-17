from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.domain.models import (
    Mission,
    MissionEvent,
    Observation,
    Position,
    SurfaceMessageRecord,
    SurfaceReplyRecord,
)
from backend.persistence.models import (
    Base,
    MissionEventRow,
    MissionSessionRow,
    ObservationRow,
    SurfaceMessageRow,
    SurfaceReplyRow,
)


@dataclass(frozen=True)
class PersistedMissionState:
    session_id: int
    mission_key: str
    mission: Mission
    position: Position
    started_at: datetime
    observations: list[Observation]
    surface_messages: list[SurfaceMessageRecord]
    surface_replies: list[SurfaceReplyRecord]
    events: list[MissionEvent]


def default_database_url() -> str:
    configured = os.getenv("DIVE_COPILOT_DATABASE_URL")
    if configured:
        return configured

    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir / 'dive_copilot.db'}"


class MissionRepository:
    """SQL-backed repository for active and historical mission sessions.

    Domain objects remain Pydantic models. The repository serializes complete
    domain records into JSON columns while keeping sessions, observations,
    communication records and events in separate relational tables. This keeps
    the V2 service layer independent from SQLAlchemy and leaves room to
    normalize individual fields later without changing the HTTP API.
    """

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or default_database_url()
        self.engine = self._create_engine(self.database_url)
        self._session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=Session,
        )
        Base.metadata.create_all(self.engine)

    @staticmethod
    def _create_engine(database_url: str) -> Engine:
        kwargs: dict = {"future": True}
        if database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if database_url in {"sqlite://", "sqlite:///:memory:"}:
                kwargs["poolclass"] = StaticPool
        return create_engine(database_url, **kwargs)

    def start_session(
        self,
        *,
        mission_key: str,
        mission: Mission,
        position: Position,
        started_at: datetime,
    ) -> int:
        with self._session_factory.begin() as db:
            db.execute(
                update(MissionSessionRow)
                .where(MissionSessionRow.active.is_(True))
                .values(active=False)
            )
            row = MissionSessionRow(
                mission_key=mission_key,
                mission_id=mission.mission_id,
                mission_data=mission.model_dump(mode="json"),
                position_data=position.model_dump(mode="json"),
                started_at=started_at,
                active=True,
            )
            db.add(row)
            db.flush()
            return row.id

    def load_active(self) -> PersistedMissionState | None:
        with self._session_factory() as db:
            row = db.scalar(
                select(MissionSessionRow)
                .where(MissionSessionRow.active.is_(True))
                .order_by(MissionSessionRow.id.desc())
                .limit(1)
            )
            if row is None:
                return None

            started_at = row.started_at
            if started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)

            return PersistedMissionState(
                session_id=row.id,
                mission_key=row.mission_key,
                mission=Mission.model_validate(row.mission_data),
                position=Position.model_validate(row.position_data),
                started_at=started_at,
                observations=self._load_models(
                    db,
                    ObservationRow,
                    row.id,
                    Observation,
                ),
                surface_messages=self._load_models(
                    db,
                    SurfaceMessageRow,
                    row.id,
                    SurfaceMessageRecord,
                ),
                surface_replies=self._load_models(
                    db,
                    SurfaceReplyRow,
                    row.id,
                    SurfaceReplyRecord,
                ),
                events=self._load_models(
                    db,
                    MissionEventRow,
                    row.id,
                    MissionEvent,
                ),
            )

    @staticmethod
    def _load_models(db: Session, row_type, session_id: int, model_type):
        rows = db.scalars(
            select(row_type)
            .where(row_type.session_id == session_id)
            .order_by(row_type.local_id.asc())
        ).all()
        return [model_type.model_validate(row.data) for row in rows]

    def save_mission(self, session_id: int, mission: Mission) -> None:
        with self._session_factory.begin() as db:
            db.execute(
                update(MissionSessionRow)
                .where(MissionSessionRow.id == session_id)
                .values(mission_data=mission.model_dump(mode="json"))
            )

    def save_position(self, session_id: int, position: Position) -> None:
        with self._session_factory.begin() as db:
            db.execute(
                update(MissionSessionRow)
                .where(MissionSessionRow.id == session_id)
                .values(position_data=position.model_dump(mode="json"))
            )

    def add_observation(self, session_id: int, observation: Observation) -> None:
        self._insert_record(
            ObservationRow,
            session_id,
            observation.id,
            observation.model_dump(mode="json"),
        )

    def update_observation(self, session_id: int, observation: Observation) -> None:
        self._update_record(
            ObservationRow,
            session_id,
            observation.id,
            observation.model_dump(mode="json"),
        )

    def add_surface_message(
        self,
        session_id: int,
        message: SurfaceMessageRecord,
    ) -> None:
        self._insert_record(
            SurfaceMessageRow,
            session_id,
            message.id,
            message.model_dump(mode="json"),
        )

    def update_surface_message(
        self,
        session_id: int,
        message: SurfaceMessageRecord,
    ) -> None:
        self._update_record(
            SurfaceMessageRow,
            session_id,
            message.id,
            message.model_dump(mode="json"),
        )

    def add_surface_reply(self, session_id: int, reply: SurfaceReplyRecord) -> None:
        self._insert_record(
            SurfaceReplyRow,
            session_id,
            reply.id,
            reply.model_dump(mode="json"),
        )

    def add_event(self, session_id: int, event: MissionEvent) -> None:
        self._insert_record(
            MissionEventRow,
            session_id,
            event.id,
            event.model_dump(mode="json"),
        )

    def _insert_record(
        self,
        row_type,
        session_id: int,
        local_id: int,
        data: dict,
    ) -> None:
        with self._session_factory.begin() as db:
            db.add(row_type(session_id=session_id, local_id=local_id, data=data))

    def _update_record(
        self,
        row_type,
        session_id: int,
        local_id: int,
        data: dict,
    ) -> None:
        with self._session_factory.begin() as db:
            db.execute(
                update(row_type)
                .where(
                    row_type.session_id == session_id,
                    row_type.local_id == local_id,
                )
                .values(data=data)
            )

    def list_sessions(self) -> list[dict]:
        """Return lightweight session metadata for diagnostics/tests."""
        with self._session_factory() as db:
            rows: Iterable[MissionSessionRow] = db.scalars(
                select(MissionSessionRow).order_by(MissionSessionRow.id.asc())
            ).all()
            return [
                {
                    "id": row.id,
                    "mission_key": row.mission_key,
                    "mission_id": row.mission_id,
                    "started_at": row.started_at.isoformat(),
                    "active": row.active,
                }
                for row in rows
            ]
