from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from backend.domain.events import EventStore
from backend.domain.models import (
    CorrectionRecord,
    DiveState,
    EventActor,
    EventType,
    Mission,
    MissionEvent,
    MissionTask,
    Observation,
    Position,
    SurfaceMessageRecord,
    SurfaceReplyRecord,
)
from backend.missions import DEFAULT_MISSION_KEY, build_mission


class MissionService:
    """Authoritative in-memory runtime for the active Dive Copilot mission.

    The HTTP API and the voice-agent tools both operate through this service.
    This keeps state transitions and event creation in one place instead of
    spreading mutation across route handlers.
    """

    def __init__(self, mission_key: str = DEFAULT_MISSION_KEY) -> None:
        self._lock = RLock()
        self._events = EventStore()
        self.active_mission_key = mission_key
        self.mission: Mission
        self.position: Position
        self.observations: list[Observation]
        self.surface_messages: list[SurfaceMessageRecord]
        self.surface_replies: list[SurfaceReplyRecord]
        self._dive_started_at = time.monotonic()
        self.reset(mission_key)

    def reset(self, mission_key: str) -> None:
        with self._lock:
            self.active_mission_key = mission_key
            self.mission = Mission.model_validate(build_mission(mission_key))
            self.position = Position(
                transect=self.mission.transect,
                marker=self.mission.start_marker,
            )
            self.observations = []
            self.surface_messages = []
            self.surface_replies = []
            self._dive_started_at = time.monotonic()

            self._events.clear()
            self._record_event(
                EventType.MISSION_STARTED,
                actor="system",
                payload={
                    "mission_key": mission_key,
                    "name": self.mission.name,
                    "site": self.mission.site,
                    "transect": self.position.transect,
                    "marker": self.position.marker,
                },
            )

    def _record_event(
        self,
        event_type: EventType,
        *,
        actor: EventActor,
        payload: dict[str, Any] | None = None,
    ) -> MissionEvent:
        return self._events.append(
            event_type=event_type,
            actor=actor,
            mission_id=self.mission.mission_id,
            payload=payload,
        )

    def mission_payload(self) -> dict[str, Any]:
        with self._lock:
            return self.mission.model_dump(mode="json")

    def current_task(self) -> MissionTask | None:
        with self._lock:
            for task in self.mission.tasks:
                if not task.completed:
                    return task
        return None

    def current_dive_state(self) -> DiveState:
        with self._lock:
            elapsed = time.monotonic() - self._dive_started_at
            base_depth = self.mission.simulation.depth_m
            depth = round(base_depth + 0.2 * math.sin(elapsed / 7), 1)
            current_task = self.current_task()

            return DiveState(
                depth_m=depth,
                dive_time_seconds=int(elapsed),
                transect=self.position.transect,
                marker=self.position.marker,
                connection="connected",
                current_task=current_task,
            )

    def complete_task(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            for task in self.mission.tasks:
                if task.id != task_id:
                    continue

                if task.completed:
                    return {
                        "status": "already_completed",
                        "task": task.model_dump(mode="json"),
                        "next_task": self._task_payload(self.current_task()),
                    }

                task.completed = True
                self._record_event(
                    EventType.TASK_COMPLETED,
                    actor="diver",
                    payload={
                        "task_id": task.id,
                        "description": task.description,
                    },
                )
                return {
                    "status": "completed",
                    "task": task.model_dump(mode="json"),
                    "next_task": self._task_payload(self.current_task()),
                }

            return {
                "status": "error",
                "message": f"Task {task_id} was not found.",
            }

    @staticmethod
    def _task_payload(task: MissionTask | None) -> dict[str, Any] | None:
        return task.model_dump(mode="json") if task else None

    def list_observations(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item.model_dump(mode="json") for item in self.observations]

    def log_observation(
        self,
        *,
        category: str,
        description: str,
        count: int | None,
    ) -> Observation:
        with self._lock:
            state = self.current_dive_state()
            item = Observation(
                id=len(self.observations) + 1,
                timestamp=datetime.now(timezone.utc),
                category=category,
                description=description,
                count=count,
                depth_m=state.depth_m,
                transect=state.transect,
                marker=state.marker,
            )
            self.observations.append(item)
            self._record_event(
                EventType.OBSERVATION_CREATED,
                actor="diver",
                payload={
                    "observation_id": item.id,
                    "category": item.category,
                    "description": item.description,
                    "count": item.count,
                    "depth_m": item.depth_m,
                    "transect": item.transect,
                    "marker": item.marker,
                },
            )
            return item

    def correct_observation(
        self,
        *,
        observation_id: int | None,
        changes: dict[str, Any],
    ) -> tuple[str, Observation | None, str | None]:
        with self._lock:
            if not self.observations:
                return "error", None, "No observations exist to correct."

            target: Observation | None = None
            if observation_id is None:
                target = self.observations[-1]
            else:
                target = next(
                    (item for item in self.observations if item.id == observation_id),
                    None,
                )

            if target is None:
                return "error", None, f"Observation {observation_id} was not found."

            if not changes:
                return "error", None, "No correction values were provided."

            previous = {
                "category": target.category,
                "description": target.description,
                "count": target.count,
            }

            for key, value in changes.items():
                setattr(target, key, value)

            corrected_at = datetime.now(timezone.utc)
            target.corrected_at = corrected_at
            target.correction_history.append(
                CorrectionRecord(
                    timestamp=corrected_at,
                    previous=previous,
                    changes=changes,
                )
            )

            self._record_event(
                EventType.OBSERVATION_CORRECTED,
                actor="diver",
                payload={
                    "observation_id": target.id,
                    "previous": previous,
                    "changes": changes,
                },
            )
            return "corrected", target, None

    def update_position(
        self,
        *,
        transect: str | None,
        marker: str | None,
    ) -> Position:
        with self._lock:
            previous = self.position.model_dump(mode="json")

            if transect is not None:
                self.position.transect = transect
            if marker is not None:
                self.position.marker = marker

            current = self.position.model_dump(mode="json")
            if current != previous:
                self._record_event(
                    EventType.POSITION_CONFIRMED,
                    actor="diver",
                    payload={"previous": previous, "position": current},
                )

            return self.position

    def list_surface_messages(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item.model_dump(mode="json") for item in self.surface_messages]

    def send_surface_message(self, *, message: str, priority: str) -> SurfaceMessageRecord:
        return self._create_surface_message(
            message=message,
            priority=priority,
            message_type="message",
        )

    def ask_surface(self, *, question: str, priority: str) -> SurfaceMessageRecord:
        return self._create_surface_message(
            message=question,
            priority=priority,
            message_type="question",
        )

    def _create_surface_message(
        self,
        *,
        message: str,
        priority: str,
        message_type: str,
    ) -> SurfaceMessageRecord:
        with self._lock:
            state = self.current_dive_state()
            item = SurfaceMessageRecord(
                id=len(self.surface_messages) + 1,
                timestamp=datetime.now(timezone.utc),
                message=message,
                priority=priority,
                depth_m=state.depth_m,
                transect=state.transect,
                marker=state.marker,
                type=message_type,  # type: ignore[arg-type]
                status="pending" if message_type == "question" else "sent",
            )
            self.surface_messages.append(item)
            self._record_event(
                EventType.SURFACE_QUESTION_SENT
                if message_type == "question"
                else EventType.SURFACE_MESSAGE_SENT,
                actor="diver",
                payload={
                    "message_id": item.id,
                    "message": item.message,
                    "priority": item.priority,
                    "transect": item.transect,
                    "marker": item.marker,
                },
            )
            return item

    def send_surface_reply(
        self,
        *,
        message: str,
        in_reply_to: int | None,
    ) -> SurfaceReplyRecord:
        with self._lock:
            item = SurfaceReplyRecord(
                id=len(self.surface_replies) + 1,
                timestamp=datetime.now(timezone.utc),
                message=message,
                in_reply_to=in_reply_to,
            )
            self.surface_replies.append(item)

            if in_reply_to is not None:
                for surface_message in self.surface_messages:
                    if surface_message.id == in_reply_to:
                        surface_message.status = "answered"
                        break

            self._record_event(
                EventType.SURFACE_REPLY_RECEIVED,
                actor="surface",
                payload={
                    "reply_id": item.id,
                    "message": item.message,
                    "in_reply_to": item.in_reply_to,
                },
            )
            return item

    def list_surface_replies(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            return [
                item.model_dump(mode="json")
                for item in self.surface_replies[-limit:]
            ]

    def list_surface_questions(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            questions = [
                item for item in self.surface_messages if item.type == "question"
            ]
            return [item.model_dump(mode="json") for item in questions[-limit:]]

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return [event.model_dump(mode="json") for event in self._events.recent(limit)]
