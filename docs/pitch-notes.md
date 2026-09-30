# Dive Copilot Pitch Notes

## Purpose

These notes support the hackathon pitch deck and final video narration.

The story should stay simple:

```text
Problem
→ Voice-first solution
→ Live proof
→ Architecture
→ Business value
→ Future direction
```

The pitch should make four judging points obvious:

- strong application of AssemblyAI technology;
- clear and understandable presentation;
- credible business value;
- originality beyond a generic voice chatbot.

---

## 1. One-Line Pitch

> **Dive Copilot turns voice communication that already happens underwater into structured, traceable and immediately usable mission data.**

Use this line in the opening slide, project description, closing slide and final spoken conclusion.

---

## 2. Short Project Description

Dive Copilot is a voice-first AI mission assistant for professional underwater operations.

It allows a diver to use natural speech to:

- retrieve the current task;
- record observations;
- correct previous observations;
- confirm physical position;
- complete mission steps;
- communicate with surface control;
- retrieve surface replies.

The prototype demonstrates this through a simulated diver HUD and surface-control interface powered by the AssemblyAI Voice Agent API.

---

## 3. The Problem

Professional underwater work creates a difficult interaction environment.

Divers may need to inspect, observe, navigate, record findings, follow procedures and communicate with surface control while their hands and visual attention are already occupied.

A conventional interface is often impractical.

Important underwater communication is valuable, but much of it remains:

```text
ephemeral
unstructured
manually transcribed
difficult to reuse operationally
```

The real problem is therefore not only speech recognition.

It is:

> How can natural voice communication become a reliable interface to structured mission state?

---

## 4. Why a Generic Voice Assistant Is Not Enough

A normal conversational assistant can answer questions, but an operational dive assistant must distinguish between different kinds of intent.

For example:

```text
"I'm heading to B4."
```

must not mean:

```text
current position = B4
```

while:

```text
"I've arrived at B4."
```

should update position.

Similarly:

```text
"Log three Pterois volitans."
```

creates an observation.

But:

```text
"Actually, make that two."
```

must modify the existing observation rather than create a duplicate.

The agent also needs to separate:

```text
mission observations
task completion
surface messages
surface questions
surface replies
```

This structured interpretation is the core of Dive Copilot.

---

## 5. The Solution

Dive Copilot provides a voice-first operational layer between the diver and mission workflow.

Natural speech is mapped to explicit tools and structured backend state.

Example:

```text
"Record moderate corrosion at support joint C2."
```

becomes:

```text
log_observation(
    category="equipment",
    description="moderate corrosion at support joint C2"
)
```

Another example:

```text
"I've reached C2."
```

becomes:

```text
update_dive_position(
    marker="C2",
    transect="C"
)
```

The agent is therefore not simply generating conversational responses.

It is performing explicit mission actions.

---

## 6. What the Prototype Demonstrates

The current prototype demonstrates:

- real-time voice interaction;
- mission-specific speech recognition context;
- tool selection;
- structured observations;
- correction of existing records;
- confirmed-position tracking;
- explicit task completion;
- diver-to-surface communication;
- surface-question workflows;
- surface-reply retrieval;
- mission switching;
- one configurable agent across multiple underwater workflows;
- a simulated diver HUD and surface-control interface.

---

## 7. Mission Scenarios

### Reef Biodiversity Survey

Focus:

```text
scientific observation
species counts
coral condition
transect progress
```

Example:

```text
"Log three Pterois volitans."
"Actually, make that two."
```

This demonstrates mission-specific terminology, structured observations and natural corrections.

### Underwater Infrastructure Inspection

Focus:

```text
corrosion
coating damage
marine growth
support joints
structural anomalies
```

Example:

```text
"Record moderate corrosion at support joint C2."
```

This is the strongest mission for the main live demo because the business case is immediately understandable.

### Marine Debris Survey

Focus:

```text
debris identification
fishing line
nets
entanglement
hazardous debris
```

This shows that the same voice architecture can adapt to environmental monitoring.

---

## 8. Application of Technology

### AssemblyAI Voice Agent API

AssemblyAI is central to the product, not added only as a transcription layer.

The prototype uses AssemblyAI for:

- real-time speech recognition;
- turn detection;
- live voice interaction;
- voice-agent orchestration;
- LLM-based tool selection;
- structured HTTP tool calling;
- spoken responses.

The browser establishes a real-time WebSocket session with the AssemblyAI Voice Agent API.

### Mission-Specific Transcription Context

Each mission has its own domain terminology.

Examples:

#### Infrastructure

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

#### Reef

```text
Pterois volitans
Acropora
Porites
coral bleaching
B1
B2
B3
B4
```

#### Marine Debris

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

The selected mission dynamically updates the live voice session with:

```text
keyterms
transcription_prompt
```

This allows one agent to adapt to multiple underwater operational domains.

---

## 9. Architecture

The high-level architecture is:

```text
Diver
  ↓
Browser UI
  ↓
AssemblyAI Voice Agent API
  ↓
Structured HTTP tools
  ↓
FastAPI Mission Backend
  ↓
Mission state + Surface Control
```

The browser also reads mission state directly from the backend for the HUD.

The important architectural principle is:

> Mission state lives outside the language model.

The LLM interprets intent and selects actions, but the backend stores:

```text
active mission
current task
position
observations
completed tasks
surface messages
surface replies
```

This makes the workflow more traceable and reduces reliance on conversational memory.

---

## 10. Example End-to-End Interaction

Diver says:

```text
"Record moderate corrosion at support joint C2."
```

Flow:

```text
speech
→ AssemblyAI transcription
→ agent intent interpretation
→ log_observation tool
→ FastAPI backend
→ structured mission record
→ spoken confirmation
→ visible observation in interface
```

This is the simplest technical story to explain during the pitch.

---

## 11. Originality

Dive Copilot is not positioned as:

```text
"ChatGPT underwater"
```

The key difference is that voice is treated as an operational interface.

The prototype handles domain-specific actions such as:

- distinguishing destination from current location;
- correcting previously stored observations;
- retrieving live surface state;
- explicitly completing mission tasks;
- dynamically adapting speech recognition to the active mission.

A useful originality statement is:

> The system is designed around the idea that a voice utterance can be a mission event, not just a message.

---

## 12. Business Value

### Core Value Proposition

Professional divers already communicate verbally during underwater work.

Dive Copilot adds value by converting part of that communication directly into structured operational data.

Potential benefits include:

- reduced manual transcription;
- improved mission traceability;
- faster creation of structured records;
- easier diver-to-surface coordination;
- clearer task progress;
- easier post-dive reporting;
- integration with existing operational systems.

Do not claim measured time savings because they have not been experimentally validated.

---

## 13. Target Users

Potential users include:

- commercial divers;
- dive supervisors;
- offshore inspection teams;
- marine engineers;
- scientific divers;
- environmental survey teams;
- aquaculture operators;
- ports and civil-infrastructure inspection teams.

---

## 14. Potential Buyers

Potential buyers include:

- commercial diving contractors;
- offshore wind operators;
- offshore energy operators;
- marine engineering companies;
- ports;
- public infrastructure operators;
- research organisations;
- environmental agencies;
- aquaculture companies.

---

## 15. Commercial Direction

The strongest commercial positioning is:

> **B2B/B2G operational software for professional underwater work.**

A realistic initial market is:

```text
commercial underwater inspection and maintenance teams
```

because they already use diver-to-surface communication and produce structured inspection records.

Dive Copilot could later integrate with:

- inspection management systems;
- asset management platforms;
- work-order systems;
- digital twins;
- maintenance databases;
- automated reporting;
- telemetry systems;
- cameras and vision models.

---

## 16. Why Infrastructure Inspection Is the Best Demo

The infrastructure-inspection scenario makes the business value immediately visible.

The judge can understand:

```text
diver sees corrosion
→ says it
→ structured observation is created
→ position is known
→ task is completed
→ surface is informed
```

This creates a clear connection between voice AI and a real operational workflow.

Use Reef and Marine Debris to show generality, not as the main demo.

---

## 17. Safety and Scope

The prototype is intentionally limited.

Dive Copilot is not:

- a dive computer;
- a decompression planner;
- an emergency-response system;
- a replacement for certified procedures;
- a replacement for a dive supervisor;
- certified diving equipment.

The prototype focuses on:

```text
mission workflow
structured observations
task tracking
surface communication
```

This boundary should be stated clearly but briefly.

---

## 18. Performance

Latency was instrumented during development.

Representative backend observation writes were approximately:

```text
1–2 ms
```

The main latency component was identified in the voice-agent model/tool-selection stage rather than the FastAPI backend.

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

The optimisation reduced latency while keeping the tested tool-routing behaviour correct.

Do not spend much pitch time on these numbers. They are useful as evidence of engineering iteration if asked.

---

## 19. Future Development

Future work could include:

- real full-face-mask communication integration;
- near-eye diver HUD hardware;
- dive-computer telemetry;
- underwater sensors;
- camera and video input;
- multimodal inspection support;
- automated post-dive reports;
- persistent mission databases;
- multi-diver coordination;
- surface-supervisor dashboards;
- degraded-connectivity operation;
- edge inference;
- integration with inspection databases and digital twins.

The long-term concept is:

```text
voice
+ telemetry
+ mission state
+ visual inspection
+ surface coordination
```

in one operational interface.

---

## 20. Suggested Pitch Deck

Keep the deck short.

### Slide 1 — Dive Copilot

Title:

```text
Dive Copilot
```

Subtitle:

```text
Voice AI for Professional Underwater Missions
```

Key line:

> Turn underwater voice communication into structured mission data.

Visual:

```text
Dive Copilot HUD screenshot
```

### Slide 2 — The Problem

Headline:

> Underwater work is hands-busy, attention-constrained and data-intensive.

Show:

```text
inspection
observations
task tracking
surface communication
```

Problem statement:

> Important mission information is often spoken during the dive but remains difficult to capture as structured operational data.

### Slide 3 — The Solution

Headline:

> Voice becomes an interface to mission state.

Show:

```text
"Record corrosion at C2."
        ↓
log_observation
        ↓
structured record
```

Also show:

```text
"I'm heading to C2."   → no position update
"I've reached C2."     → position update
```

### Slide 4 — How It Works

Architecture:

```text
Diver
↓
Browser / HUD
↓
AssemblyAI Voice Agent
↓
Structured tools
↓
Mission backend
↓
Surface Control
```

Highlight AssemblyAI:

```text
real-time speech
mission-aware context
tool selection
voice response
```

### Slide 5 — Three Missions, One Agent

Show three cards:

```text
Reef Biodiversity Survey
Underwater Infrastructure Inspection
Marine Debris Survey
```

Key point:

> The same agent dynamically adapts its speech context, terminology and mission workflow.

### Slide 6 — Business Value

Headline:

> From spoken observations to usable operational data.

Show:

```text
less manual transcription
better traceability
structured records
surface coordination
integration potential
```

Potential sectors:

```text
commercial diving
offshore wind
marine infrastructure
scientific diving
environmental monitoring
```

### Slide 7 — Future Vision

Headline:

> From prototype to operational dive platform.

Show:

```text
full-face mask
+
near-eye HUD
+
telemetry
+
camera
+
surface systems
```

Closing line:

> Dive Copilot turns voice communication that already happens underwater into structured, traceable and immediately usable mission data.

---

## 21. Suggested 60-Second Verbal Pitch

> Professional divers often need to inspect structures, record observations, follow mission tasks and communicate with surface control while their hands and attention are already occupied.

> Dive Copilot is a voice-first AI mission assistant that turns this communication into structured operational actions.

> A diver can say, "Record moderate corrosion at support joint C2," and the system creates a structured observation. They can correct it naturally, confirm their position, complete tasks and communicate with surface control.

> AssemblyAI powers the real-time voice interaction, mission-aware transcription and tool selection, while a FastAPI backend maintains the actual mission state.

> The prototype supports infrastructure inspection, reef surveying and marine-debris missions using one configurable agent.

> The long-term opportunity is an operational software layer for commercial diving and underwater inspection, connecting voice, telemetry, visual data and existing asset-management systems.

---

## 22. Suggested 20-Second Elevator Pitch

> Dive Copilot is a voice-first mission assistant for professional divers. It uses AssemblyAI to turn natural underwater communication into structured mission actions such as observations, position updates, task completion and surface communication. Instead of being just an underwater chatbot, it uses voice as an interface to operational state.

---

## 23. Key Phrases to Reuse

Use these consistently across the submission, video and slides:

> **Voice AI for professional underwater missions.**

> **Voice as an interface to operational state.**

> **Structured, traceable mission data.**

> **One configurable agent across multiple underwater workflows.**

> **Mission-aware speech recognition.**

> **Turn underwater voice communication into structured mission data.**

---

## 24. Claims to Avoid

Do not claim that Dive Copilot:

- is production-ready;
- is certified for underwater use;
- has been tested underwater;
- improves safety by a measured percentage;
- reduces inspection time by a measured percentage;
- works offline today;
- integrates with real dive computers today;
- automatically detects diver arrival;
- replaces the dive supervisor;
- replaces certified procedures.

Use:

```text
prototype
simulation
proof of concept
future integration
potential value
```

where appropriate.

---

## 25. Final Pitch Principle

Do not spend the pitch explaining every tool or technical detail.

The audience should leave understanding three things:

```text
1. The problem is real.
2. Voice creates structured mission actions.
3. The same architecture can support real professional underwater workflows.
```

Final line:

> **Dive Copilot turns voice communication that already happens underwater into structured, traceable and immediately usable mission data.**
