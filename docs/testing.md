# Dive Copilot Testing

## 1. Purpose

This document summarises the manual functional and latency testing performed for the Dive Copilot hackathon prototype.

The goal of testing was to verify that the voice agent:

- selects the correct operational tool;
- preserves mission state correctly;
- distinguishes planned movement from confirmed position;
- records and corrects observations;
- completes tasks only when explicitly requested;
- separates diver-to-surface messages, questions and replies;
- adapts speech-recognition context to the active mission;
- keeps backend processing latency low enough for interactive use.

The prototype was tested primarily through the browser interface while inspecting the live voice transcript, tool calls, FastAPI logs and browser timing instrumentation.

---

## 2. Test Environment

### Voice Layer

- AssemblyAI Voice Agent API
- real-time WebSocket voice session
- mission-specific keyterms and transcription prompt
- structured HTTP tool calls
- streamed voice responses

### Backend

- Python
- FastAPI
- Uvicorn
- in-memory simulated mission state

### Frontend

- browser-based Dive Copilot HUD
- JavaScript
- Web Audio API
- AudioWorklet capture and playback
- live transcript and tool-call visibility

### Missions

The following mission configurations were used during testing:

```text
reef-survey
infrastructure-inspection
marine-debris
```

---

## 3. Infrastructure Inspection Acceptance Test

The infrastructure-inspection mission was used for the most complete end-to-end acceptance test.

### 3.1 Observation Logging

Input:

```text
Record moderate corrosion at support joint C2.
```

Observed tool call:

```text
log_observation({
  "category": "equipment",
  "description": "moderate corrosion at support joint C2"
})
```

Result:

```text
PASS
```

The observation was written to structured mission state.

---

### 3.2 Ambiguous / Misrecognised Input

Observed transcript:

```text
Average C2.
```

Observed tool call:

```text
get_dive_state({})
```

Agent response:

```text
I am sorry, I am not sure what you mean by average C2. Could you please clarify?
```

Result:

```text
PASS
```

The agent did not perform an unsafe state-changing write from unclear speech.

---

### 3.3 Confirmed Position Update

Input:

```text
I have reached C2.
```

Observed tool call:

```text
update_dive_position({
  "marker": "C2",
  "transect": "C"
})
```

Result:

```text
PASS
```

The confirmed current position was updated correctly.

---

### 3.4 Observation Correction

Input:

```text
Actually make that slight corrosion.
```

Observed tool call:

```text
correct_observation({
  "description": "slight corrosion at support joint C2"
})
```

Result:

```text
PASS
```

The existing observation was modified rather than duplicated.

---

### 3.5 Task Completion

Input:

```text
Inspection of C2 is complete.
```

Observed tool sequence:

```text
get_dive_state({})
complete_task({
  "task_id": "task-1"
})
```

Result:

```text
PASS
```

The agent first resolved the current task and then completed the correct task.

---

## 4. Surface Communication Testing

Surface communication was tested separately because three different operations must remain distinct:

```text
message_surface
ask_surface
get_surface_messages
```

### 4.1 Surface Question

Input:

```text
Ask surface if they want to close inspection.
```

Observed tool call:

```text
ask_surface({
  "priority": "routine",
  "question": "Do you want to close the inspection?"
})
```

Result:

```text
PASS
```

The request was treated as a question rather than as a normal message.

---

### 4.2 Surface Reply Retrieval

Input:

```text
Anything back from surface?
```

Observed tool call:

```text
get_surface_messages({})
```

Result when no reply existed:

```text
No replies from surface yet.
```

Later, after a simulated reply was available:

```text
Anything back from the surface?
```

Observed tool call:

```text
get_surface_messages({})
```

Result:

```text
Surface says to proceed with the mission.
```

Result:

```text
PASS
```

The final implementation was adjusted so that requests for current surface state are retrieved through the backend rather than answered only from conversational memory.

---

### 4.3 Incomplete Surface Message

An early test used:

```text
Tell surface visibility.
```

The first implementation incorrectly sent:

```text
message_surface({
  "message": "Visibility.",
  "priority": "routine"
})
```

This was considered a failure because the message content was incomplete.

The agent instructions and tool description were then tightened so that fragmentary messages require clarification rather than being sent.

Result after correction:

```text
FIXED IN AGENT RULES
```

---

### 4.4 False Proactive Notification

An early surface-question response included:

```text
I will let you know as soon as they reply.
```

This was considered incorrect because the prototype does not independently push a reply notification to the diver.

The prompt was updated so that the agent does not promise future monitoring or notification capabilities that are not implemented.

Result:

```text
FIXED IN AGENT RULES
```

---

## 5. Reef Survey Acceptance Test

The reef-survey mission was used to verify mission-specific terminology, observation correction and position semantics.

### 5.1 Species Recognition and Observation Logging

Input:

```text
Log 3 Pterois volitans.
```

Observed tool call:

```text
log_observation({
  "category": "species",
  "count": 3,
  "description": "Pterois volitans"
})
```

Result:

```text
PASS
```

The scientific species name was transcribed and routed correctly.

---

### 5.2 Count Correction

Follow-up:

```text
You need to make that 2.
```

Observed tool call:

```text
correct_observation({
  "count": 2
})
```

Result:

```text
PASS
```

The existing observation was corrected instead of creating another record.

---

### 5.3 Planned Movement Must Not Update Position

Input:

```text
I'm heading to B5.
```

Observed behaviour:

```text
No update_dive_position tool call.
```

Result:

```text
PASS
```

The intended destination was not stored as current physical position.

A follow-up correction:

```text
No, B4.
```

also did not update position.

Result:

```text
PASS
```

---

### 5.4 Confirmed Arrival

Input:

```text
I've arrived at B4.
```

Observed tool call:

```text
update_dive_position({
  "marker": "B4"
})
```

Result:

```text
PASS
```

Only explicit arrival confirmation changed the stored position.

---

### 5.5 Proactive Arrival Promise

During one reef test, the agent responded to planned movement with:

```text
I'll let you know when you arrive at B5.
```

and later:

```text
I'll let you know when you arrive at B4.
```

This was considered incorrect because the prototype does not independently detect arrival.

The prompt and position-tool description were updated so that the agent must not promise automatic arrival monitoring.

Status:

```text
REQUIRES FINAL SMOKE RE-TEST
```

---

## 6. Mission-Specific Speech Context

The backend exposes mission-specific speech context containing:

```text
keyterms
transcription_prompt
```

The browser injects this context into the live AssemblyAI session after the session becomes ready.

### Infrastructure Inspection Context

Verified terminology included:

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
C5
```

### Reef Survey Context

Verified terminology included:

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
B5
```

### Marine Debris Context

Configured terminology includes:

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
D5
```

Result:

```text
PASS
```

Mission-specific context was successfully loaded into the live voice session.

---

## 7. Backend Latency Testing

FastAPI request timing middleware was added to measure backend processing time.

A representative observation write produced:

```text
POST /api/observations 1.7 ms
```

Other local GET requests were typically in the low-millisecond range.

Examples observed during testing included approximately:

```text
3–11 ms
```

Result:

```text
PASS
```

The mission backend was not the main source of perceived voice latency.

---

## 8. End-to-End Voice Latency

Browser instrumentation was added around voice-agent events.

The main measured stages were:

```text
speech stopped → final transcript
speech stopped → tool call
speech stopped → first reply phase
speech stopped → first audio
final transcript → first audio
last reply start → first audio
```

### Initial Measured Run

Representative values:

```text
speech stopped → final transcript      ~1 ms
speech stopped → tool call          ~2190 ms
speech stopped → first audio        ~2860 ms
last reply start → first audio       ~444 ms
```

The largest delay occurred between the final transcript and tool selection.

---

## 9. Prompt Optimisation

The system prompt was shortened while preserving:

- tool-routing rules;
- position semantics;
- observation correction;
- surface communication boundaries;
- clarification rules;
- safety constraints.

After prompt optimisation, a representative run produced:

```text
speech stopped → final transcript      ~5 ms
speech stopped → tool call          ~1845 ms
speech stopped → first audio        ~2554 ms
last reply start → first audio       ~398 ms
```

Approximate improvement:

```text
tool-selection path     ~345 ms faster
first-audio latency     ~306 ms faster
```

The tool call remained correct after the optimisation.

Result:

```text
PASS
```

The optimisation reduced latency without breaking the tested observation workflow.

---

## 10. Important Behavioural Rules Verified

The following behaviour was explicitly tested or observed during acceptance testing.

| Behaviour | Status |
|---|---|
| Log structured observation | PASS |
| Correct existing observation | PASS |
| Recognise mission-specific terminology | PASS |
| Planned movement does not update position | PASS |
| Confirmed arrival updates position | PASS |
| Explicit task completion | PASS |
| Ask surface a question | PASS |
| Retrieve current surface reply | PASS |
| Avoid stale surface-state answers | PASS after prompt fix |
| Clarify ambiguous state-changing speech | PASS |
| Reject incomplete surface-message fragments | Fixed in agent rules |
| Avoid false proactive surface notifications | Fixed in agent rules |
| Avoid false proactive arrival notifications | Needs final smoke re-test |

---

## 11. Remaining Smoke Tests Before Final Submission

The following tests are intentionally short and should be performed against the public deployment.

### Infrastructure Inspection

```text
"Record moderate corrosion at support joint C2."
"I've reached C2."
"Ask surface if they want a closer inspection."
"Anything back from surface?"
```

### Reef Survey

```text
"Log three Pterois volitans."
"Actually, make that two."
"I'm heading to B4."
"I've arrived at B4."
```

Confirm that planned movement does not trigger a position update and that the agent no longer promises to detect arrival automatically.

### Marine Debris Survey

```text
"Log monofilament at D3."
"Tell surface hazardous debris found at D3."
```

### Interface

Verify:

```text
mission selection
mission switching
reset simulation
LISTENING → PROCESSING → SPEAKING → LISTENING
```

### Voice Interruption

Interrupt the agent while it is speaking and confirm that playback stops and the new user turn is accepted.

---

## 12. Known Prototype Limitations

The current test environment is a simulation.

Testing does not validate:

- underwater microphone hardware;
- full-face-mask audio;
- underwater acoustic communication;
- real dive-computer telemetry;
- real depth sensors;
- certified safety behaviour;
- production database persistence;
- multi-user concurrency;
- degraded or offline connectivity.

The tests validate the software architecture and the behaviour of the voice-driven mission workflow.

---

## 13. Test Conclusion

The core Dive Copilot workflow was successfully demonstrated across the infrastructure-inspection and reef-survey scenarios.

The strongest verified behaviours are:

- voice-driven structured observation logging;
- correction of previously stored data;
- explicit separation of intended movement and confirmed physical position;
- explicit task completion;
- mission-aware speech recognition;
- structured diver-to-surface communication;
- retrieval of live surface state through backend tools;
- low-latency mission-backend operations.

The largest measured latency component was the language-model/tool-selection stage rather than FastAPI processing.

The remaining work before final submission is limited to a small public-deployment smoke test, especially for the final proactive-arrival rule and the marine-debris scenario.
