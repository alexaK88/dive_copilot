import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.missions import (
    DEFAULT_MISSION_KEY,
    get_mission_speech_context,
    list_missions,
)
from backend.services.mission_service import MissionService

app = FastAPI(title="Dive Copilot API", version="0.2.0")

# Fine for the current public prototype. Lock this down to the deployed frontend
# origin before treating the service as production infrastructure.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

mission_service = MissionService(DEFAULT_MISSION_KEY)


class MissionSelection(BaseModel):
    mission_id: str


class SurfaceQuestion(BaseModel):
    question: str
    priority: str = "routine"


class SurfaceReply(BaseModel):
    message: str
    in_reply_to: int | None = None


class DivePositionUpdate(BaseModel):
    transect: str | None = None
    marker: str | None = None


class SurfaceMessage(BaseModel):
    message: str
    priority: str = "routine"


class TaskCompletion(BaseModel):
    task_id: str


class ObservationIn(BaseModel):
    category: str
    description: str
    count: int | None = None


class ObservationCorrection(BaseModel):
    observation_id: int | None = None
    category: str | None = None
    description: str | None = None
    count: int | None = None


@app.middleware("http")
async def measure_request_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[LATENCY] {request.method} {request.url.path} {elapsed_ms:.1f} ms")
    return response


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_version": app.version,
        "active_mission_id": mission_service.active_mission_key,
    }


@app.get("/api/missions")
def get_available_missions():
    return {
        "missions": list_missions(),
        "active_mission_id": mission_service.active_mission_key,
    }


@app.post("/api/mission/select")
def select_mission(selection: MissionSelection):
    try:
        mission_service.reset(selection.mission_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Mission not found") from exc

    return {
        "status": "selected",
        "mission_id": mission_service.active_mission_key,
        "mission": mission_service.mission_payload(),
        "dive_state": mission_service.current_dive_state().model_dump(mode="json"),
        "speech_context": get_mission_speech_context(
            mission_service.active_mission_key
        ),
    }


@app.get("/api/mission")
def get_mission():
    return mission_service.mission_payload()


@app.get("/api/dive-state")
def get_dive_state():
    return mission_service.current_dive_state().model_dump(mode="json")


@app.post("/api/dive-state/position")
def update_dive_position(update: DivePositionUpdate):
    position = mission_service.update_position(
        transect=update.transect,
        marker=update.marker,
    )
    return {
        "status": "updated",
        "position": position.model_dump(mode="json"),
    }


@app.get("/api/observations")
def get_observations():
    observations = mission_service.list_observations()
    return {
        "count": len(observations),
        "observations": observations,
    }


@app.post("/api/observations")
def log_observation(observation: ObservationIn):
    item = mission_service.log_observation(
        category=observation.category,
        description=observation.description,
        count=observation.count,
    )
    return {
        "status": "recorded",
        "observation": item.model_dump(mode="json"),
    }


@app.post("/api/observations/correct")
def correct_observation(correction: ObservationCorrection):
    changes: dict[str, Any] = correction.model_dump(
        exclude_unset=True,
        exclude={"observation_id"},
    )
    status, observation, message = mission_service.correct_observation(
        observation_id=correction.observation_id,
        changes=changes,
    )

    if status == "error":
        return {"status": "error", "message": message}

    return {
        "status": "corrected",
        "observation": observation.model_dump(mode="json") if observation else None,
    }


@app.post("/api/tasks/complete")
def complete_task(completion: TaskCompletion):
    return mission_service.complete_task(completion.task_id)


@app.get("/api/surface/messages")
def get_surface_messages():
    messages = mission_service.list_surface_messages()
    return {
        "count": len(messages),
        "messages": messages,
    }


@app.post("/api/surface/messages")
def send_surface_message(surface_message: SurfaceMessage):
    item = mission_service.send_surface_message(
        message=surface_message.message,
        priority=surface_message.priority,
    )
    return {
        "status": "sent",
        "message": item.model_dump(mode="json"),
    }


@app.post("/api/surface/questions")
def ask_surface(question: SurfaceQuestion):
    item = mission_service.ask_surface(
        question=question.question,
        priority=question.priority,
    )
    return {
        "status": "sent",
        "request": item.model_dump(mode="json"),
    }


@app.post("/api/surface/replies")
def send_surface_reply(reply: SurfaceReply):
    item = mission_service.send_surface_reply(
        message=reply.message,
        in_reply_to=reply.in_reply_to,
    )
    return {
        "status": "received",
        "reply": item.model_dump(mode="json"),
    }


@app.get("/api/surface/replies")
def get_surface_replies():
    messages = mission_service.list_surface_replies(limit=10)
    return {
        "count": len(mission_service.surface_replies),
        "messages": messages,
    }


@app.get("/api/surface/questions")
def get_surface_questions():
    questions = mission_service.list_surface_questions(limit=10)
    total_questions = sum(
        1 for item in mission_service.surface_messages if item.type == "question"
    )
    return {
        "count": total_questions,
        "questions": questions,
    }


@app.get("/api/events")
def get_events(limit: int = Query(default=100, ge=1, le=500)):
    events = mission_service.events(limit=limit)
    return {
        "count": len(events),
        "events": events,
    }


@app.get("/api/mission/timeline")
def get_mission_timeline(limit: int = Query(default=100, ge=1, le=500)):
    """Human/UI-facing alias for the structured mission event stream."""
    events = mission_service.events(limit=limit)
    return {
        "mission_id": mission_service.mission.mission_id,
        "count": len(events),
        "events": events,
    }
