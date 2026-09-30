# Dive Copilot Demo Script

## Purpose

This script is designed for the final hackathon demo video.

Target duration:

```text
4:00–4:45
```

The goal is to demonstrate:

- the problem Dive Copilot solves;
- real-time AssemblyAI voice interaction;
- structured tool use;
- mission-aware speech recognition;
- mission-state updates;
- observation correction;
- position semantics;
- task completion;
- surface communication;
- multiple mission configurations;
- practical business value.

The demo should focus on one mission in depth and show the other missions briefly.

Do not try to demonstrate every feature.

---

# 1. Before Recording

## 1.1 Open the Public Demo

Open the deployed Dive Copilot application.

Make sure:

```text
frontend is online
backend health is OK
AssemblyAI agent is published
mission service is reachable
microphone permission is enabled
```

Use the public deployment, not localhost.

---

## 1.2 Reset the Simulation

Before recording:

```text
Reset Simulation
```

Then select:

```text
Underwater Infrastructure Inspection
```

Confirm that the interface shows:

```text
Offshore Structure A
current task
mission progress
voice controls
surface communication
mission observations
```

---

## 1.3 Prepare Surface Reply

If the Surface Control interface allows a reply to be entered manually, prepare:

```text
Proceed with the inspection.
```

Do not submit it until the surface-reply part of the demo.

---

## 1.4 Use Exact Demo Phrases

The commands below were selected because they exercise important behaviours and have already been tested.

Avoid improvising during the main recording unless necessary.

---

# 2. Video Structure

Recommended timing:

```text
0:00–0:30   Introduction and problem
0:30–0:50   Solution overview
0:50–3:10   Live infrastructure demo
3:10–3:40   Mission switching
3:40–4:15   Architecture and AssemblyAI
4:15–4:45   Business value and future direction
```

---

# 3. Opening

## 0:00–0:30 — Problem

### Narration

> Professional divers often need to inspect structures, record observations, follow mission tasks and communicate with surface control while their hands and attention are already occupied.

> Dive Copilot explores whether voice AI can become an operational interface for this environment, rather than simply acting as an underwater chatbot.

While speaking, show the main Dive Copilot interface.

Do not interact with the agent yet.

---

# 4. Solution Overview

## 0:30–0:50

### Narration

> Dive Copilot connects natural speech to structured mission state. A diver can ask for the current task, record findings, correct previous observations, confirm position, complete mission steps and communicate with surface control.

> The prototype uses AssemblyAI for real-time voice interaction and tool selection, with a FastAPI backend maintaining the actual mission state.

Then start the voice connection.

Wait for:

```text
Dive Copilot online. Ready for mission support.
```

---

# 5. Main Live Demo — Infrastructure Inspection

## 0:50–3:10

This is the main technical demonstration.

Keep the interface visible so judges can see:

```text
live transcript
tool calls
current task
observations
mission progress
surface communication
```

---

## Step 1 — Ask for Current Task

Say:

> What's my current task?

Expected behaviour:

```text
get_dive_state
```

Expected response should identify the current infrastructure-inspection task.

### Narration after response

> The current task is not stored only in conversation memory. The agent retrieves it from the mission backend.

Keep this explanation brief.

---

## Step 2 — Record an Observation

Say clearly:

> Record moderate corrosion at support joint C2.

Expected tool call:

```text
log_observation({
  "category": "equipment",
  "description": "moderate corrosion at support joint C2"
})
```

Expected result:

```text
observation appears in Mission Observations
```

### Narration

> The spoken observation has become structured mission data rather than remaining only in the transcript.

---

## Step 3 — Demonstrate Position Semantics

First say:

> I'm heading to C2.

Expected behaviour:

```text
NO update_dive_position tool call
```

The agent may acknowledge the destination, but the stored position should not change.

Then say:

> I've reached C2.

Expected tool call:

```text
update_dive_position({
  "marker": "C2",
  "transect": "C"
})
```

### Narration

> Dive Copilot distinguishes intended movement from confirmed physical position. Heading to C2 does not update the location, but explicitly reaching C2 does.

This is one of the strongest behaviours to show.

---

## Step 4 — Correct Previous Data

Say:

> Actually, make that slight corrosion.

Expected tool call:

```text
correct_observation({
  "description": "slight corrosion at support joint C2"
})
```

Expected result:

```text
existing observation is corrected
no duplicate observation is created
```

### Narration

> The diver can correct a previous observation naturally without creating a second conflicting record.

---

## Step 5 — Complete the Task

Say:

> Inspection of C2 is complete.

Expected behaviour:

```text
get_dive_state
complete_task({
  "task_id": "task-1"
})
```

Expected result:

```text
mission progress updates
next task becomes current
```

### Narration

> Task completion is explicit. Reaching the location or logging an observation does not automatically complete the task.

---

## Step 6 — Surface Communication

Say:

> Ask surface if they want a closer inspection.

Expected tool call:

```text
ask_surface({
  "question": "Do you want a closer inspection?"
})
```

Expected result:

```text
question appears in surface communication
```

### Narration

> Surface communication is handled separately from the mission record.

If available, now enter the prepared surface reply:

```text
Proceed with the inspection.
```

Then say:

> Anything back from surface?

Expected tool call:

```text
get_surface_messages({})
```

Expected response:

```text
Surface says to proceed with the inspection.
```

### Narration

> Surface replies are retrieved as live external state instead of being invented from conversational memory.

---

# 6. Mission Switching

## 3:10–3:40

End or pause the current voice session if required.

Click:

```text
Change Mission
```

Select:

```text
Reef Biodiversity Survey
```

Show the new mission details and task list.

### Narration

> Dive Copilot uses one configurable agent across different underwater workflows.

> When the mission changes, the live voice session receives mission-specific speech context, including specialist terminology and marker identifiers.

If time permits, start the Reef mission and say:

> Log three Pterois volitans.

Expected tool call:

```text
log_observation({
  "category": "species",
  "count": 3,
  "description": "Pterois volitans"
})
```

Then say:

> Actually, make that two.

Expected:

```text
correct_observation({
  "count": 2
})
```

Do not spend longer than about 20–25 seconds on this mission.

---

# 7. Briefly Show the Third Mission

Still within the mission-selection screen, briefly show:

```text
Marine Debris Survey
```

You do not need to run another full voice interaction.

### Narration

> The same architecture also supports a marine-debris survey, with its own tasks, terminology and operational context.

This demonstrates generality without making the video too long.

---

# 8. Architecture and AssemblyAI

## 3:40–4:15

Show either:

- the architecture diagram in the README or `architecture.md`; or
- the application while describing the architecture.

### Narration

> The browser streams live audio to the AssemblyAI Voice Agent API.

> AssemblyAI handles real-time transcription, voice-agent orchestration, tool selection and spoken responses.

> The agent then calls structured HTTP tools for mission actions such as observations, position, task completion and surface communication.

> Mission state is stored outside the language model in the FastAPI backend, so operational state remains explicit and traceable.

If showing the architecture, use this simplified flow:

```text
Diver
  ↓
Browser UI
  ↓
AssemblyAI Voice Agent
  ↓
Structured HTTP Tools
  ↓
Dive Copilot Mission Backend
  ↓
Mission State / Surface Control
```

---

# 9. Business Value

## 4:15–4:35

### Narration

> The commercial idea is not to replace dive computers or certified safety procedures.

> Dive Copilot is an operational software layer for professional underwater work.

> It can turn voice communication that already happens during a dive into structured, traceable and immediately usable mission data.

> Potential users include commercial diving contractors, offshore inspection teams, marine infrastructure operators and scientific diving organisations.

---

# 10. Closing

## 4:35–4:45

### Narration

> The next step would be integration with full-face-mask communications, real telemetry, cameras and existing inspection systems.

> Dive Copilot demonstrates how voice AI can move beyond conversation and become an interface to real operational workflows.

End on the main Dive Copilot screen.

---

# 11. Exact Main Demo Command Sequence

Use this sequence during the primary recording:

```text
1. "What's my current task?"

2. "Record moderate corrosion at support joint C2."

3. "I'm heading to C2."

4. "I've reached C2."

5. "Actually, make that slight corrosion."

6. "Inspection of C2 is complete."

7. "Ask surface if they want a closer inspection."

8. [Surface enters: "Proceed with the inspection."]

9. "Anything back from surface?"
```

Optional Reef demonstration:

```text
10. Change mission → Reef Biodiversity Survey

11. "Log three Pterois volitans."

12. "Actually, make that two."
```

---

# 12. What Not to Demonstrate

Do not deliberately test unstable or unnecessary edge cases in the final video.

Avoid:

```text
very long hesitant utterances
unusual phrasing not previously tested
multiple corrections in one complex sentence
network stress tests
latency debugging
developer console
Render logs
ngrok
localhost
```

The final demo should show the product, not the debugging process.

---

# 13. If Voice Recognition Mishears a Phrase

Do not panic or restart immediately.

If the agent safely asks for clarification, this can actually demonstrate the clarification behaviour.

Correct it naturally.

Example:

```text
Agent: "Could you clarify the marker?"

You: "C2."
```

Continue the demo.

Restart only if:

```text
the wrong state-changing tool is called
the application disconnects
the mission state becomes visibly incorrect
```

---

# 14. If a Tool Call Fails

If a tool fails during recording:

1. stop the recording;
2. verify backend health;
3. verify the public backend URL;
4. verify the AssemblyAI agent is pointing to the deployed backend;
5. reset the simulation;
6. restart the recording.

Do not explain infrastructure debugging in the final video.

---

# 15. If Surface Reply Is Unreliable

If the manual surface-reply workflow is not completely stable before recording, omit that part.

Keep:

```text
"Ask surface if they want a closer inspection."
```

Then narrate:

> The question is now available to Surface Control through a separate structured communication channel.

Do not risk the whole demo for one optional reply interaction.

---

# 16. Recording Checklist

Immediately before recording, verify:

```text
[ ] public frontend opens
[ ] backend /health returns OK
[ ] correct AssemblyAI agent is active
[ ] Infrastructure Inspection selected
[ ] simulation reset
[ ] microphone works
[ ] transcript visible
[ ] tool calls visible
[ ] observations panel visible
[ ] mission progress visible
[ ] surface panel visible
[ ] browser notifications/popups closed
[ ] unnecessary tabs closed
[ ] no secrets visible
```

---

# 17. Presentation Priorities

The demo should make four judging points obvious.

## Application of Technology

Show:

```text
real-time voice
mission-aware transcription
tool selection
structured state updates
barge-in capable voice interface
```

## Presentation

Keep the workflow visually simple:

```text
speak
→ tool call
→ visible state change
```

## Business Value

Emphasise:

```text
hands-free operation
reduced manual transcription
structured mission records
traceability
surface coordination
```

## Originality

Emphasise:

> Dive Copilot is not a generic underwater chatbot.

> Voice is being used as an operational interface to mission state.

---

# 18. Final Message

The one sentence judges should remember is:

> **Dive Copilot turns voice communication that already happens underwater into structured, traceable and immediately usable mission data.**
