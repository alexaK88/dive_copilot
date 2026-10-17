from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MissionTask(BaseModel):
    id: str
    description: str
    completed: bool = False


class MissionSimulation(BaseModel):
    summary: str
    depth_m: float


class Mission(BaseModel):
    mission_id: str
    name: str
    description: str
    site: str
    diver: str
    transect: str
    start_marker: str
    status: str = "active"
    simulation: MissionSimulation
    tasks: list[MissionTask]


class Position(BaseModel):
    transect: str
    marker: str


class DiveState(BaseModel):
    depth_m: float
    dive_time_seconds: int
    transect: str
    marker: str
    connection: str
    current_task: MissionTask | None = None


class CorrectionRecord(BaseModel):
    timestamp: datetime
    previous: dict[str, Any]
    changes: dict[str, Any]


class Observation(BaseModel):
    id: int
    timestamp: datetime
    category: str
    description: str
    count: int | None = None
    depth_m: float
    transect: str
    marker: str
    corrected_at: datetime | None = None
    correction_history: list[CorrectionRecord] = Field(default_factory=list)


class SurfaceMessageRecord(BaseModel):
    id: int
    timestamp: datetime
    message: str
    priority: str
    depth_m: float
    transect: str
    marker: str
    type: Literal["message", "question"] = "message"
    status: Literal["sent", "pending", "answered"] = "sent"


class SurfaceReplyRecord(BaseModel):
    id: int
    timestamp: datetime
    message: str
    in_reply_to: int | None = None


class EventType(str, Enum):
    MISSION_STARTED = "MISSION_STARTED"
    POSITION_CONFIRMED = "POSITION_CONFIRMED"
    OBSERVATION_CREATED = "OBSERVATION_CREATED"
    OBSERVATION_CORRECTED = "OBSERVATION_CORRECTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    SURFACE_MESSAGE_SENT = "SURFACE_MESSAGE_SENT"
    SURFACE_QUESTION_SENT = "SURFACE_QUESTION_SENT"
    SURFACE_REPLY_RECEIVED = "SURFACE_REPLY_RECEIVED"


EventActor = Literal["system", "diver", "surface"]


class MissionEvent(BaseModel):
    id: int
    type: EventType
    timestamp: datetime
    actor: EventActor
    mission_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
