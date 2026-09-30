# Dive Copilot Architecture

## 1. Overview

Dive Copilot is a voice-first mission assistant for professional underwater operations.

The prototype combines:

- a browser-based diver and surface-control interface;
- the AssemblyAI Voice Agent API;
- mission-specific speech context;
- structured HTTP tool calls;
- a FastAPI mission backend;
- simulated mission state and telemetry.

The architecture is designed so that conversational voice input is translated into explicit operational actions.

Examples include:

```text
"Record moderate corrosion at support joint C2."
→ log observation

"I've reached C2."
→ update confirmed position

"Inspection of C2 is complete."
→ complete mission task

"Ask surface if they want a closer inspection."
→ send question to surface control
```

The system therefore separates natural-language interaction from structured mission state.

---

## 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                     Diver Browser UI                    │
│                                                         │
│  Mission HUD                                            │
│  Live voice transcript                                  │
│  Mission observations                                   │
│  Surface communication                                  │
│  Mission selection                                      │
│  Simulated telemetry                                    │
└───────────────┬─────────────────────────────┬───────────┘
                │                             │
                │ WebSocket                   │ HTTP
                │ voice session               │ mission data
                │                             │
                ▼                             ▼
┌─────────────────────────────┐   ┌────────────────────────┐
│ AssemblyAI Voice Agent API  │   │ FastAPI Mission Backend│
│                             │   │                        │
│ Speech recognition          │   │ Missions               │
│ Turn detection              │   │ Tasks                  │
│ LLM reasoning               │   │ Position               │
│ Tool selection              │   │ Observations           │
│ Voice generation            │   │ Surface messages       │
└──────────────┬──────────────┘   │ Surface replies        │
               │                  └────────────────────────┘
               │ HTTP tool calls             ▲
               └─────────────────────────────┘
```

---

## 3. Main Components

### 3.1 Browser Application

The browser application is the main user interface.

It provides:

- mission selection;
- microphone capture;
- live voice connection;
- voice transcript;
- mission status;
- current task;
- mission progress;
- simulated telemetry;
- structured observations;
- surface communication;
- simulation reset;
- mission switching.

The browser application communicates with two separate services:

1. the AssemblyAI Voice Agent API for real-time voice interaction;
2. the Dive Copilot mission backend for mission state and UI updates.

This separation allows the voice layer and mission-state layer to evolve independently.

---

## 4. Voice Session Architecture

The browser establishes a real-time WebSocket connection with the AssemblyAI Voice Agent API.

The voice pipeline is:

```text
Microphone
   ↓
Web Audio API
   ↓
AudioWorklet
   ↓
PCM audio
   ↓
WebSocket
   ↓
AssemblyAI Voice Agent API
```

The agent returns:

```text
speech events
transcripts
tool calls
generated audio
session events
```

Generated audio is streamed back to the browser and played through a dedicated playback AudioWorklet.

The browser also supports interruption or barge-in.

When new user speech is detected while the agent is speaking, current playback is stopped so that the new user turn can be processed.

---

## 5. Mission-Specific Speech Context

Dive Copilot uses one configurable voice agent across multiple mission types.

Each mission provides its own speech-recognition context.

For example, the infrastructure inspection mission includes terms such as:

```text
support joint
corrosion
protective coating
marine growth
structural anomaly
C1
C2
C3
C4
```

The reef mission includes terminology such as:

```text
Pterois volitans
Acropora
Porites
coral bleaching
fish population
B1
B2
B3
B4
```

The marine-debris mission includes terms such as:

```text
monofilament
fishing net
entanglement
hazardous debris
D1
D2
D3
D4
```

After a mission is selected, the browser receives:

```text
keyterms
transcription_prompt
```

from the mission backend.

These values are then sent into the live AssemblyAI session through a session update.

The result is a single agent whose speech-recognition context changes according to the selected underwater mission.

---

## 6. Agent Layer

The Dive Copilot agent is configured using:

```text
agents/dive_copilot.jsonc
```

Its system prompt is stored separately in:

```text
agents/prompts/dive_copilot.txt
```

The agent is responsible for:

- interpreting natural-language intent;
- deciding whether information retrieval is required;
- choosing the appropriate tool;
- extracting structured arguments;
- requesting clarification when required;
- generating concise voice responses.

The agent itself does not directly own mission state.

Mission state is maintained by the backend and accessed through tools.

This reduces the risk of treating conversational memory as authoritative operational state.

---

## 7. Tool Architecture

The agent interacts with the mission backend through HTTP tools.

The main tool groups are:

### 7.1 Mission Information

```text
get_mission
get_dive_state
```

Used to retrieve the active mission and current operational state.

### 7.2 Observations

```text
log_observation
get_observations
correct_observation
```

Used to create, retrieve and modify structured observations.

### 7.3 Position

```text
update_dive_position
```

Used only for confirmed current physical position.

The design deliberately separates:

```text
"I'm heading to B4."
```

from:

```text
"I've arrived at B4."
```

Only the second statement changes the stored position.

### 7.4 Tasks

```text
complete_task
```

Used to explicitly mark mission tasks as complete.

A task is not completed merely because:

- the diver reached its location;
- a related observation was recorded;
- the task was discussed.

### 7.5 Surface Communication

```text
message_surface
ask_surface
get_surface_messages
```

These tools separate three distinct operations:

```text
send information to surface
ask surface a question
retrieve actual surface replies
```

This is important because a sent question does not imply that an answer has already been received.

Fresh surface-state queries are retrieved through the backend rather than answered only from conversation history.

---

## 8. Mission Backend

The mission backend is implemented in FastAPI.

It maintains the simulated operational state used by both the browser interface and the voice agent.

The main state includes:

```text
active mission
current position
mission timer
current task
completed tasks
observations
surface messages
surface questions
surface replies
```

The backend currently uses in-memory state because the project is a hackathon prototype.

A production implementation could replace this with persistent storage.

---

## 9. Mission Configuration

Mission definitions are stored separately from agent logic.

Each mission contains information such as:

```text
mission ID
mission name
site
transect
starting marker
base depth
task list
speech-recognition keyterms
transcription context
```

The currently implemented missions are:

```text
reef-survey
infrastructure-inspection
marine-debris
```

This design allows new mission types to be introduced without creating a completely separate voice agent.

---

## 10. Example End-to-End Flow

Consider the following command:

```text
"Record moderate corrosion at support joint C2."
```

The sequence is:

```text
1. Diver speaks.
       ↓
2. Browser streams audio to AssemblyAI.
       ↓
3. AssemblyAI transcribes the utterance.
       ↓
4. Voice agent identifies an observation-recording intent.
       ↓
5. Agent selects log_observation.
       ↓
6. Structured arguments are generated:

   category = equipment
   description = moderate corrosion at support joint C2

       ↓
7. AssemblyAI sends the HTTP tool request to the Dive Copilot backend.
       ↓
8. Backend stores the observation with current mission context.
       ↓
9. Backend returns success.
       ↓
10. Agent produces a short spoken confirmation.
       ↓
11. Browser receives generated audio.
       ↓
12. Mission observation appears in the interface.
```

---

## 11. Position Update Example

Input:

```text
"I'm heading to B4."
```

Expected behavior:

```text
No position write.
```

The agent understands this as planned movement.

Input:

```text
"I've arrived at B4."
```

Expected behavior:

```text
update_dive_position(marker="B4")
```

The backend then updates the confirmed current position.

This distinction prevents planned destinations from corrupting mission state.

---

## 12. Observation Correction Example

Input:

```text
"Log three Pterois volitans."
```

Tool call:

```text
log_observation(
    category="species",
    description="Pterois volitans",
    count=3
)
```

Later:

```text
"Actually, make that two."
```

Tool call:

```text
correct_observation(
    count=2
)
```

The previous record is modified instead of creating a duplicate observation.

---

## 13. Surface Communication Example

Input:

```text
"Ask surface if they want a closer inspection."
```

Tool:

```text
ask_surface
```

The question is stored for surface control.

Later:

```text
"Anything back from surface?"
```

The agent calls:

```text
get_surface_messages
```

rather than relying on an earlier conversational answer.

This keeps live external state separate from model memory.

---

## 14. Deployment Architecture

The deployed prototype uses Render for public hosting.

The browser application and mission backend are separate web services.

```text
                           Internet
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
     ┌─────────────────────┐     ┌─────────────────────┐
     │ Public Browser App  │     │ Public Mission API  │
     │       Render        │     │       Render        │
     └──────────┬──────────┘     └──────────▲──────────┘
                │                           │
                │ WebSocket                 │ HTTP tools
                ▼                           │
     ┌─────────────────────┐                │
     │ AssemblyAI Voice    │────────────────┘
     │ Agent API           │
     └─────────────────────┘
```

The final public architecture removes the development dependency on:

```text
localhost
ngrok
```

The AssemblyAI tools communicate directly with the deployed mission backend.

---

## 15. Security

The AssemblyAI API key is never exposed directly in browser JavaScript.

The browser application requests a temporary session token from its server-side component.

The permanent API key is stored as a deployment environment variable.

Secrets such as:

```text
ASSEMBLYAI_API_KEY
```

must not be committed to the repository.

---

## 16. Performance

Latency instrumentation was added during development to identify the main delay in voice interactions.

Testing showed that backend operations were completed in the low-millisecond range.

For example, observation writes were measured at approximately:

```text
1–2 ms
```

The larger latency component occurred between final transcription and tool selection inside the voice-agent pipeline.

Prompt simplification was used to reduce this delay while preserving tool-routing behaviour.

This distinction was useful because it showed that the mission backend itself was not the performance bottleneck.

---

## 17. Prototype Boundaries

The current implementation is a simulation.

It does not currently connect to:

- a physical full-face diving mask;
- a dive computer;
- real depth sensors;
- underwater acoustic communication hardware;
- production inspection databases;
- certified safety systems.

Simulated telemetry is used to demonstrate the interaction model.

The prototype is intended to validate the software architecture and voice workflow before integration with physical underwater systems.

---

## 18. Future Architecture

A production version could extend the architecture with:

```text
Dive Computer
      │
      ├── depth
      ├── gas
      └── telemetry
      │
      ▼

Dive Copilot
      │
      ├── Voice Agent
      ├── Mission Engine
      ├── Camera / Vision
      ├── Sensor Fusion
      └── Local Safety Boundaries
      │
      ▼

Surface Control
      │
      ├── Live Mission Dashboard
      ├── Asset Management
      ├── Inspection Database
      ├── Work Orders
      └── Automated Reports
```

Additional production considerations would include:

- persistent storage;
- authentication;
- role-based access;
- mission audit logs;
- degraded-connectivity operation;
- offline or edge processing;
- encrypted diver-to-surface communication;
- multi-diver coordination;
- device telemetry;
- camera and video integration;
- integration with enterprise inspection systems.

---

## 19. Design Principle

The central architectural principle of Dive Copilot is:

> **Voice should be an interface to operational state, not merely a conversational layer.**

Speech is therefore translated into explicit mission actions whose results are stored outside the language model.

This allows Dive Copilot to combine natural interaction with structured, traceable mission data.
