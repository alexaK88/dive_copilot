from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.domain.models import EventActor, EventType, MissionEvent


class EventStore:
    """Small in-memory append-only event store for one active mission session.

    Persistence comes in a later V2 phase. Keeping event creation behind this
    class means the API and mission service do not need to change when the
    backing store moves to SQLite/PostgreSQL.
    """

    def __init__(self) -> None:
        self._events: list[MissionEvent] = []
        self._next_id = 1

    def clear(self) -> None:
        self._events.clear()
        self._next_id = 1

    def append(
        self,
        *,
        event_type: EventType,
        actor: EventActor,
        mission_id: str,
        payload: dict[str, Any] | None = None,
    ) -> MissionEvent:
        event = MissionEvent(
            id=self._next_id,
            type=event_type,
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            mission_id=mission_id,
            payload=payload or {},
        )
        self._next_id += 1
        self._events.append(event)
        return event

    def all(self) -> list[MissionEvent]:
        return list(self._events)

    def recent(self, limit: int = 100) -> list[MissionEvent]:
        if limit <= 0:
            return []
        return list(self._events[-limit:])
