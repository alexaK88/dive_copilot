import math
import time
from datetime import datetime, timezone
from http.client import HTTPException

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.missions import (DEFAULT_MISSION_KEY, build_mission, get_mission_speech_context, list_missions)

app = FastAPI(title="Dive Copilot API")

# Fine for our local hackathon demo.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

DIVE_STARTED_AT = time.time()
ACTIVE_MISSION_KEY = DEFAULT_MISSION_KEY
MISSION = build_mission(ACTIVE_MISSION_KEY)

DIVE_CONTEXT = {
    "transect": MISSION["transect"],
    "marker": MISSION["start_marker"]}

OBSERVATIONS = []
SURFACE_MESSAGES = []
SURFACE_REPLIES = []


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


def get_current_task():
    for task in MISSION["tasks"]:
        if not task["completed"]:
            return task

    return None


@app.get("/api/surface/messages")
def get_surface_messages():
    return {
        "count": len(SURFACE_MESSAGES),
        "messages": SURFACE_MESSAGES}


@app.post("/api/surface/messages")
def send_surface_message(surface_message: SurfaceMessage):
    state = current_dive_state()

    item = {
        "id": len(SURFACE_MESSAGES) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": surface_message.message,
        "priority": surface_message.priority,
        "depth_m": state["depth_m"],
        "transect": state["transect"],
        "marker": state["marker"]}

    SURFACE_MESSAGES.append(item)

    return {
        "status": "sent",
        "message": item}


@app.get("/api/missions")
def get_available_missions():
    return {
        "missions": list_missions(),
        "active_mission_id": ACTIVE_MISSION_KEY}


@app.post("/api/mission/select")
def select_mission(selection: MissionSelection):
    try:
        reset_simulation(selection.mission_id)

    except KeyError:
        raise HTTPException(status_code=404, detail="Mission not found")

    return {
        "status": "selected",
        "mission_id": ACTIVE_MISSION_KEY,
        "mission": MISSION,
        "dive_state": current_dive_state(),

        "speech_context": get_mission_speech_context(ACTIVE_MISSION_KEY), }


@app.middleware("http")
async def measure_request_time(request: Request, call_next, ):
    start = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"[LATENCY] "
          f"{request.method} "
          f"{request.url.path} "
          f"{elapsed_ms:.1f} ms")

    return response


@app.post("/api/tasks/complete")
def complete_task(completion: TaskCompletion):
    for task in MISSION["tasks"]:
        if task["id"] == completion.task_id:

            if task["completed"]:
                return {
                    "status": "already_completed",
                    "task": task,
                    "next_task": get_current_task()}

            task["completed"] = True

            return {
                "status": "completed",
                "task": task,
                "next_task": get_current_task()}

    return {
        "status": "error",
        "message": f"Task {completion.task_id} was not found."}


def current_dive_state():
    elapsed = time.time() - DIVE_STARTED_AT
    base_depth = MISSION["simulation"]["depth_m"]

    depth = round(base_depth + 0.2 * math.sin(elapsed / 7), 1)

    return {
        "depth_m": depth,
        "dive_time_seconds": int(elapsed),
        "transect": DIVE_CONTEXT["transect"],
        "marker": DIVE_CONTEXT["marker"],
        "connection": "connected",
        "current_task": get_current_task()}


@app.get("/health")
def health():
    return {
        "status": "ok"}


@app.get("/api/mission")
def get_mission():
    return MISSION


@app.get("/api/dive-state")
def get_dive_state():
    return current_dive_state()


@app.get("/api/observations")
def get_observations():
    return {
        "count": len(OBSERVATIONS),
        "observations": OBSERVATIONS}


@app.post("/api/observations")
def log_observation(observation: ObservationIn):
    state = current_dive_state()

    item = {
        "id": len(OBSERVATIONS) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": observation.category,
        "description": observation.description,
        "count": observation.count,
        "depth_m": state["depth_m"],
        "transect": state["transect"],
        "marker": state["marker"]}

    OBSERVATIONS.append(item)

    return {
        "status": "recorded",
        "observation": item}


@app.post("/api/observations/correct")
def correct_observation(correction: ObservationCorrection):
    if not OBSERVATIONS:
        return {
            "status": "error",
            "message": "No observations exist to correct."}

    # If no ID is supplied, correct the most recent observation.
    target = None

    if correction.observation_id is None:
        target = OBSERVATIONS[-1]
    else:
        for observation in OBSERVATIONS:
            if observation["id"] == correction.observation_id:
                target = observation
                break

    if target is None:
        return {
            "status": "error",
            "message": f"Observation {correction.observation_id} was not found."}

    changes = correction.model_dump(exclude_unset=True, exclude={"observation_id"})

    if not changes:
        return {
            "status": "error",
            "message": "No correction values were provided."}

    # Keep a small audit trail.
    previous = {
        "category": target.get("category"),
        "description": target.get("description"),
        "count": target.get("count")}

    for key, value in changes.items():
        target[key] = value

    target["corrected_at"] = datetime.now(timezone.utc).isoformat()

    target.setdefault("correction_history", []).append({
        "timestamp": target["corrected_at"],
        "previous": previous,
        "changes": changes})

    return {
        "status": "corrected",
        "observation": target}


@app.post("/api/dive-state/position")
def update_dive_position(update: DivePositionUpdate):
    if update.transect is not None:
        DIVE_CONTEXT["transect"] = update.transect

    if update.marker is not None:
        DIVE_CONTEXT["marker"] = update.marker

    return {
        "status": "updated",
        "position": {
            "transect": DIVE_CONTEXT["transect"],
            "marker": DIVE_CONTEXT["marker"]}}


@app.post("/api/surface/questions")
def ask_surface(question: SurfaceQuestion):
    state = current_dive_state()

    item = {
        "id": len(SURFACE_MESSAGES) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "question",
        "message": question.question,
        "priority": question.priority,
        "depth_m": state["depth_m"],
        "transect": state["transect"],
        "marker": state["marker"],
        "status": "pending"}

    SURFACE_MESSAGES.append(item)

    return {
        "status": "sent",
        "request": item}


@app.post("/api/surface/replies")
def send_surface_reply(reply: SurfaceReply):
    item = {
        "id": len(SURFACE_REPLIES) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": reply.message,
        "in_reply_to": reply.in_reply_to}

    SURFACE_REPLIES.append(item)

    if reply.in_reply_to is not None:
        for message in SURFACE_MESSAGES:
            if message["id"] == reply.in_reply_to:
                message["status"] = "answered"
                break

    return {
        "status": "received",
        "reply": item}


@app.get("/api/surface/replies")
def get_surface_replies():
    return {
        "count": len(SURFACE_REPLIES),
        "messages": SURFACE_REPLIES[-10:]}


@app.get("/api/surface/questions")
def get_surface_questions():
    questions = [item for item in SURFACE_MESSAGES if item.get("type") == "question"]

    return {
        "count": len(questions),
        "questions": questions[-10:]}


def reset_simulation(mission_key: str) -> None:
    global ACTIVE_MISSION_KEY
    global MISSION
    global DIVE_CONTEXT
    global DIVE_STARTED_AT

    ACTIVE_MISSION_KEY = mission_key
    MISSION = build_mission(mission_key)
    DIVE_CONTEXT = {
        "transect": MISSION["transect"],
        "marker": MISSION["start_marker"]}

    DIVE_STARTED_AT = time.time()

    OBSERVATIONS.clear()
    SURFACE_MESSAGES.clear()
    SURFACE_REPLIES.clear()
