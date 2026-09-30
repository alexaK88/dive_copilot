# Dive Copilot — Hackathon Submission

## Project Title

**Dive Copilot**

---

## Short Description

Dive Copilot is a voice-first AI mission assistant for professional underwater operations. It uses AssemblyAI to turn natural speech into structured mission actions such as observation logging, position updates, task completion and diver-to-surface communication.

---

## Long Description

Dive Copilot explores how voice AI can become an operational interface for professional underwater work.

Divers often need to inspect structures, record findings, follow mission tasks and communicate with surface control while their hands and visual attention are already occupied. Important information is frequently communicated verbally during the dive, but that information may later need to be manually reconstructed, transcribed or entered into another system.

Dive Copilot addresses this by connecting natural speech directly to structured mission state.

A diver can say:

```text
"Record moderate corrosion at support joint C2."
```

and the system creates a structured observation.

They can say:

```text
"I've reached C2."
```

and the system updates confirmed position.

They can correct previous information:

```text
"Actually, make that slight corrosion."
```

complete a task:

```text
"Inspection of C2 is complete."
```

or communicate with surface control:

```text
"Ask surface if they want a closer inspection."
```

The prototype is built around one central idea:

> **Voice should be an interface to operational state, not merely a conversational layer.**

The current implementation combines the AssemblyAI Voice Agent API, mission-specific speech context, structured HTTP tools, a FastAPI mission backend and a browser-based simulated diver HUD / surface-control interface.

The prototype currently supports three mission scenarios:

- Underwater Infrastructure Inspection;
- Reef Biodiversity Survey;
- Marine Debris Survey.

The same configurable agent adapts to each mission by changing its speech-recognition context, terminology and mission workflow.

---

## Problem

Professional underwater work is interaction-constrained.

A diver may need to:

- inspect structures;
- identify biological or environmental findings;
- follow a sequence of mission tasks;
- track position;
- communicate with surface control;
- document observations.

At the same time:

- hands may already be occupied;
- visual attention is limited;
- environmental conditions may be noisy;
- communication is time-sensitive;
- observations need to become usable mission records.

A purely conversational assistant is not enough.

An operational assistant must understand the difference between:

```text
"I'm heading to B4."
```

and:

```text
"I've arrived at B4."
```

The first describes an intended destination.

The second confirms current physical position.

Likewise:

```text
"Log three Pterois volitans."
```

should create a structured observation, while:

```text
"Actually, make that two."
```

should correct the existing observation instead of creating a duplicate.

The core challenge is therefore not only speech recognition.

It is reliable, context-aware translation from natural voice interaction into structured mission actions.

---

## Solution

Dive Copilot provides a hands-free conversational layer between the diver and the mission workflow.

The agent supports:

- current mission and task retrieval;
- structured observation logging;
- observation correction;
- confirmed position tracking;
- explicit task completion;
- diver-to-surface messaging;
- questions to surface control;
- retrieval of surface replies;
- mission switching;
- mission-specific speech context.

Actions are deliberately separated.

For example:

```text
"Record corrosion at C2."
```

is treated as an observation.

```text
"Tell surface corrosion found at C2."
```

is treated as communication.

```text
"Ask surface if they want a closer inspection."
```

is treated as a question requiring a surface response.

The backend stores the actual operational state so that the language model does not need to act as the source of truth.

---

## How Dive Copilot Works

The high-level flow is:

```text
Diver
  ↓
Browser UI / Simulated HUD
  ↓
AssemblyAI Voice Agent API
  ↓
Structured HTTP Tool Calls
  ↓
FastAPI Mission Backend
  ↓
Mission State + Surface Control
```

The browser handles:

- microphone capture;
- real-time WebSocket connection;
- live transcript;
- streamed voice playback;
- mission HUD;
- observations;
- surface communication;
- mission selection.

AssemblyAI handles:

- real-time speech recognition;
- turn detection;
- voice-agent orchestration;
- LLM interaction;
- tool selection;
- voice generation.

The FastAPI backend maintains:

- active mission;
- task list;
- current task;
- confirmed position;
- completed tasks;
- observations;
- surface messages;
- surface questions;
- surface replies.

---

## Key Features

### Real-Time Voice Interaction

Dive Copilot uses the AssemblyAI Voice Agent API for continuous speech interaction.

The browser streams microphone audio through a WebSocket session and receives transcripts, tool calls and generated audio.

### Mission-Aware Speech Recognition

Each mission provides its own speech context.

For example, infrastructure inspection includes terms such as:

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

The Reef Survey includes terms such as:

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

The Marine Debris Survey includes:

```text
monofilament
fishing line
fishing net
entanglement
hazardous debris
D1
D2
D3
D4
```

When the mission changes, the live voice session receives new:

```text
keyterms
transcription_prompt
```

This allows one agent to adapt to multiple professional underwater domains.

### Structured Observation Logging

A spoken finding becomes a structured mission record.

Example:

```text
"Record moderate corrosion at support joint C2."
```

Tool call:

```text
log_observation({
  "category": "equipment",
  "description": "moderate corrosion at support joint C2"
})
```

### Natural Correction

The diver can correct a previously stored observation using ordinary speech.

Example:

```text
"Actually, make that slight corrosion."
```

Tool call:

```text
correct_observation({
  "description": "slight corrosion at support joint C2"
})
```

This modifies the original record rather than creating a duplicate.

### Confirmed Position Tracking

Dive Copilot separates intended movement from confirmed location.

```text
"I'm heading to B4."
```

does not update position.

```text
"I've arrived at B4."
```

does.

This distinction prevents navigation intent from being incorrectly stored as physical position.

### Explicit Task Completion

Mission tasks are completed only when the diver explicitly confirms completion.

Reaching a location or recording a related observation does not automatically complete the task.

### Two-Way Surface Communication

The system separates:

```text
message_surface
ask_surface
get_surface_messages
```

This allows:

- statements to surface control;
- questions requiring a response;
- retrieval of actual replies.

The agent does not treat a sent question as if it had already received an answer.

### Interruption / Barge-In

If the diver begins speaking while the agent is still responding, current audio playback is stopped so that the new user turn can be processed.

This is important for fast operational interaction.

---

## Mission Scenarios

### 1. Underwater Infrastructure Inspection

Site:

```text
Offshore Structure A
```

Tasks include:

- inspecting support joints;
- recording corrosion or marine growth;
- checking protective coating;
- reporting structural anomalies.

Example command:

```text
"Record moderate corrosion at support joint C2."
```

This is the primary demonstration scenario because it clearly connects voice AI to an industrial inspection workflow.

### 2. Reef Biodiversity Survey

Site:

```text
Reef Sector B
```

Tasks include:

- surveying fish population;
- recording coral bleaching;
- completing observations along the transect.

Example:

```text
"Log three Pterois volitans."
```

Correction:

```text
"Actually, make that two."
```

This scenario demonstrates scientific terminology and natural correction.

### 3. Marine Debris Survey

Site:

```text
Coastal Survey Sector D
```

Tasks include:

- recording debris type and quantity;
- identifying fishing gear;
- detecting entanglement;
- reporting hazardous debris.

Example:

```text
"Log monofilament at D3."
```

This demonstrates adaptation to an environmental-monitoring workflow.

---

## Application of Technology

AssemblyAI is central to the implementation.

Dive Copilot uses the AssemblyAI Voice Agent API for:

- real-time voice interaction;
- speech recognition;
- turn detection;
- mission-aware transcription context;
- LLM-based tool selection;
- structured HTTP tool calling;
- generated voice responses.

The project also uses live session updates so that mission-specific keyterms and transcription prompts can be injected after a mission is selected.

This means the same stored agent can adapt dynamically rather than requiring a separate agent per mission.

The browser application uses Web Audio API and AudioWorklet processing for microphone capture and streamed playback.

The mission backend is implemented in FastAPI and exposes structured endpoints for mission state and agent actions.

---

## Business Value

Dive Copilot is intended as a B2B / B2G operational software layer for professional underwater work.

Potential users include:

- commercial divers;
- dive supervisors;
- offshore inspection teams;
- marine engineers;
- scientific divers;
- environmental survey teams;
- aquaculture operators.

Potential buyers include:

- commercial diving contractors;
- offshore wind operators;
- offshore energy operators;
- marine engineering companies;
- ports;
- public infrastructure operators;
- research organisations;
- environmental agencies.

The key commercial idea is:

> **Turn voice communication that already happens underwater into structured, traceable and immediately usable mission data.**

Potential benefits include:

- reduced manual transcription;
- improved mission traceability;
- structured inspection records;
- faster post-dive reporting;
- clearer task progress;
- easier diver-to-surface coordination;
- integration with existing operational systems.

The prototype does not claim measured time savings or production-level performance. The goal is to validate the interaction model and software architecture.

---

## Originality

Dive Copilot is not designed as a generic underwater chatbot.

The system treats voice as an operational interface.

A spoken utterance can become:

- a mission observation;
- a position update;
- a task-completion event;
- a message to surface control;
- a question to surface control;
- a correction to previously stored data.

The prototype also distinguishes subtle but operationally important differences such as:

```text
destination ≠ confirmed position
```

and:

```text
surface question ≠ surface reply
```

Another original aspect is the use of mission-specific speech context within one configurable agent.

The same voice assistant can move between scientific, industrial and environmental missions while adapting its terminology and operational context.

---

## System Architecture

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

The browser application and mission backend are deployed separately.

The deployed architecture does not depend on localhost or ngrok.

Mission state is stored outside the language model.

---

## Technology Stack

### Voice AI

- AssemblyAI Voice Agent API
- real-time transcription
- live session updates
- mission-specific keyterms
- transcription prompts
- structured HTTP tools
- generated speech

### Backend

- Python
- FastAPI
- Uvicorn

### Frontend

- HTML
- CSS
- JavaScript
- WebSocket
- Web Audio API
- AudioWorklet

### Deployment

- Render
- AssemblyAI hosted voice infrastructure

---

## User Experience

The prototype includes a browser-based simulated diver HUD and Surface Control view.

The interface shows:

- active mission;
- current task;
- mission progress;
- simulated telemetry;
- listening / processing / speaking state;
- live voice transcript;
- tool actions;
- structured observations;
- surface communication;
- mission activity;
- mission selection;
- reset controls.

The goal is to make the voice agent understandable to a first-time user and visible to hackathon judges.

---

## Safety and Scope

Dive Copilot is a research and hackathon prototype.

It is not:

- a dive computer;
- a decompression planner;
- an emergency-response system;
- certified diving equipment;
- a replacement for a qualified dive supervisor;
- a replacement for certified diving procedures.

The current implementation focuses on:

- mission workflow;
- observation capture;
- task tracking;
- position semantics;
- surface communication.

Safety-critical decisions should remain with certified procedures, appropriate equipment and qualified personnel.

---

## Testing and Evaluation

The prototype was manually tested across the Infrastructure Inspection and Reef Survey scenarios.

Verified behaviours include:

- mission-specific speech context;
- structured observation logging;
- correction of previous observations;
- current-task retrieval;
- planned movement not changing position;
- confirmed arrival changing position;
- explicit task completion;
- surface question sending;
- surface reply retrieval;
- clarification before ambiguous state changes;
- mission switching;
- backend latency measurement.

FastAPI observation writes were measured at approximately:

```text
1–2 ms
```

The largest measured latency component was the language-model / tool-selection stage rather than backend processing.

A representative interaction initially measured approximately:

```text
speech stopped → tool call       ~2190 ms
speech stopped → first audio     ~2860 ms
```

After simplifying the system prompt:

```text
speech stopped → tool call       ~1845 ms
speech stopped → first audio     ~2554 ms
```

This improved latency without breaking the tested tool-selection behaviour.

More detailed test notes are available in:

```text
docs/testing.md
```

---

## Limitations

The current prototype uses simulated mission state and telemetry.

It does not currently integrate with:

- a physical full-face diving mask;
- real dive-computer telemetry;
- real underwater positioning;
- underwater acoustic communication hardware;
- production inspection systems;
- persistent production databases;
- certified safety systems.

The prototype is intended to demonstrate the interaction model and system architecture.

---

## Future Work

Future development could include:

- full-face-mask communication integration;
- near-eye diver HUD hardware;
- real dive-computer telemetry;
- underwater sensors;
- visual input from diver cameras;
- multimodal inspection support;
- automated post-dive reports;
- persistent mission databases;
- multi-diver coordination;
- supervisor dashboards;
- offline / edge operation;
- degraded-connectivity handling;
- integration with asset-management systems;
- integration with inspection databases;
- work-order integration;
- digital-twin integration.

The long-term direction is an operational platform combining:

```text
voice
+ telemetry
+ mission state
+ visual inspection
+ surface coordination
```

---

## Repository

Public GitHub repository:

```text
https://github.com/alexaK88/dive-copilot
```

---

## Live Demo

Public application:

```text
ADD_PUBLIC_RENDER_FRONTEND_URL_HERE
```

---

## Backend Health

Public mission API health endpoint:

```text
ADD_PUBLIC_RENDER_BACKEND_URL_HERE/health
```

---

## Video

Demo video:

```text
ADD_VIDEO_URL_HERE
```

---

## Pitch Deck

Slide presentation:

```text
ADD_PITCH_DECK_URL_HERE
```

---

## Documentation

Additional project documentation:

```text
docs/architecture.md
docs/testing.md
docs/demo-script.md
docs/pitch-notes.md
```

---

## Suggested Technology Tags

```text
AssemblyAI
Voice AI
Voice Agent
Speech Recognition
AI Agents
FastAPI
Real-Time AI
Maritime
Underwater Robotics
Industrial Inspection
Environmental Monitoring
Human-AI Interaction
```

---

## Suggested Category Tags

Use the closest categories available in the submission form.

Recommended themes:

```text
AI / Machine Learning
Voice AI
Developer Tools / Infrastructure
Industrial Technology
Climate / Environment
Productivity
Future of Work
```

---

## Final Summary

Dive Copilot demonstrates how real-time voice AI can become a practical interface for environments where conventional interaction is difficult.

Instead of keeping communication only inside a conversation, the system translates speech into explicit mission actions whose results are stored as structured operational state.

The prototype combines:

```text
real-time voice
mission-aware transcription
tool calling
structured mission state
surface communication
multiple mission workflows
```

in one configurable system.

The central idea is simple:

> **Dive Copilot turns voice communication that already happens underwater into structured, traceable and immediately usable mission data.**
