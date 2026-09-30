# Dive Copilot

**Voice AI for professional underwater missions.**

Dive Copilot is a voice-first AI mission assistant designed to support professional divers during underwater operations.

Instead of acting as a conventional chatbot, Dive Copilot connects natural voice interaction to structured mission state. Divers can use speech to access their current task, record observations, update confirmed position, complete mission steps and communicate with surface control while remaining focused on the underwater environment.

The current prototype demonstrates this workflow through a browser-based simulated dive interface powered by the AssemblyAI Voice Agent API.

---

## The Problem

Professional underwater work creates a difficult interaction environment.

Divers may need to inspect structures, record biological observations, identify hazards, follow mission tasks and communicate with surface control while their hands and attention are already occupied.

Information gathered underwater must also be converted into usable mission records. In many workflows, this means observations communicated verbally during the dive later need to be manually interpreted, transcribed or transferred into another system.

The challenge is therefore not simply speech recognition.

An underwater assistant needs to understand:

- what mission is currently active;
- what task the diver is performing;
- where the diver has actually confirmed their position;
- what observations have already been recorded;
- whether the diver is correcting previous information;
- whether a statement is intended for the mission record or for surface control;
- and when incomplete or ambiguous speech requires clarification.

Dive Copilot explores how a voice agent can turn underwater communication into structured, context-aware mission actions.

---

## The Solution

Dive Copilot provides a hands-free conversational layer between the diver and the mission workflow.

A diver can say:

> "What's my current task?"

and receive the current mission task.

They can report an observation:

> "Record moderate corrosion at support joint C2."

which becomes structured mission data.

They can confirm movement:

> "I've reached C2."

which updates their confirmed current position.

They can correct previous information:

> "Actually, make that slight corrosion."

without creating a duplicate observation.

They can communicate with the surface team:

> "Ask surface if they want a closer inspection."

and later check:

> "Anything back from surface?"

The voice interaction is therefore connected to explicit operational actions rather than relying only on conversational memory.

---

## Mission Scenarios

The prototype currently supports three simulated underwater missions.

### Reef Biodiversity Survey

A scientific survey along Reef Sector B.

The diver can:

- survey fish populations;
- record species observations;
- document coral bleaching;
- move between transect markers;
- correct species counts;
- complete survey tasks.

Example:

> "Log three Pterois volitans."

> "Wait, make that two."

---

### Underwater Infrastructure Inspection

An inspection of Offshore Structure A.

The diver can:

- inspect support joints;
- record corrosion;
- document coating damage;
- identify marine growth;
- record structural anomalies;
- communicate findings to surface control.

Example:

> "Record moderate corrosion at support joint C2."

---

### Marine Debris Survey

An environmental survey in Coastal Survey Sector D.

The diver can:

- record debris type and quantity;
- identify fishing line or nets;
- record entanglement hazards;
- report hazardous debris;
- coordinate recovery-related information with surface control.

Example:

> "Log monofilament at D3."

---

## How It Works

Dive Copilot combines real-time voice interaction with a structured mission backend.

```text
                         ┌──────────────────────┐
                         │   AssemblyAI Voice   │
                         │      Agent API       │
                         └──────────┬───────────┘
                                    │
                          speech + tool calls
                                    │
                                    ▼
┌──────────────────┐      ┌──────────────────────┐
│                  │      │                      │
│   Diver Browser  │◄────►│     Dive Copilot     │
│       UI         │      │        Agent         │
│                  │      │                      │
└────────┬─────────┘      └──────────┬───────────┘
         │                           │
         │ mission state             │ HTTP tools
         │                           │
         ▼                           ▼
┌───────────────────────────────────────────────┐
│              Mission Backend                  │
│                                               │
│  Missions · Tasks · Position · Observations   │
│       Surface Messages · Surface Replies      │
└───────────────────────────────────────────────┘