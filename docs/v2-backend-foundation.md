# Dive Copilot V2 — Backend Foundation

This increment begins the V2 migration from a hackathon-style collection of global dictionaries/lists to an explicit mission domain and event-driven runtime.

## What changed

- Added typed domain models for missions, tasks, observations, positions, dive state, surface communication, and mission events.
- Added `MissionService` as the single owner of active mission state and all state-changing operations.
- Added an append-only in-memory `EventStore`.
- Every important state transition now produces a structured mission event.
- Existing API routes and response shapes were kept compatible with the current diver HUD and AssemblyAI HTTP tools.
- Added `/api/events` and `/api/mission/timeline` for the V2 timeline/operations UI.
- Added backend unit tests for the most important state-transition rules.

## Current event types

- `MISSION_STARTED`
- `POSITION_CONFIRMED`
- `OBSERVATION_CREATED`
- `OBSERVATION_CORRECTED`
- `TASK_COMPLETED`
- `SURFACE_MESSAGE_SENT`
- `SURFACE_QUESTION_SENT`
- `SURFACE_REPLY_RECEIVED`

## Important design rule

The backend is now the authoritative owner of mission state. Route handlers should validate HTTP input and delegate behavior to `MissionService`; they should not independently mutate mission data.

## Compatibility

The following existing endpoints remain available with the same intent and compatible response structures:

- `/api/missions`
- `/api/mission/select`
- `/api/mission`
- `/api/dive-state`
- `/api/dive-state/position`
- `/api/observations`
- `/api/observations/correct`
- `/api/tasks/complete`
- `/api/surface/messages`
- `/api/surface/questions`
- `/api/surface/replies`

This means the current AssemblyAI agent definition and browser HUD do not need to be redesigned as part of this backend increment.

## Next step

Replace the in-memory collections and `EventStore` with repositories backed by SQLite during development and PostgreSQL in deployment. The `MissionService` API is intentionally designed so that persistence can be introduced without moving mission rules back into the route layer.
