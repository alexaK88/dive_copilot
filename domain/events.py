from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.domain.models import EventActor, EventType, MissionEvent


class EventStore:
    """In-process event view for the active mission session.

    The authoritative durable copy is written through MissionRepository. This
    small store keeps event sequencing and recent-event reads fast while the
    service is running, and can be rehydrated after a restart.
    """

    def __init__(self, events: list[MissionEvent] | None = None) -> None:
        self._events: list[MissionEvent] = []
        self._next_id = 1
        if events:
            self.load(events)

    def clear(self) -> None:
        self._events.clear()
        self._next_id = 1

    def load(self, events: list[MissionEvent]) -> None:
        self._events = list(events)
        self._next_id = max((event.id for event in self._events), default=0) + 1

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
