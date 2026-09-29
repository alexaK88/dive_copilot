# Dive Copilot — Hackathon Submission

## Project Title
Dive Copilot

## Short Description

## Long Description

## Problem
## Problem

#### 1. Underwater work is an interaction-constrained environment

Professional diving takes place in an environment where traditional user interfaces are difficult to use. A diver may already be using both hands to inspect equipment, collect samples, operate tools, control buoyancy or navigate through a survey area. At the same time, the diver must remain aware of the mission, their position, the surrounding environment and communication with the surface team.
This makes even simple digital interactions more difficult than they would be on land. Reaching for a device, navigating menus or manually entering data introduces friction into a workflow where attention is already divided across multiple operational tasks.

#### 2. Important observations have to be captured while the mission is happening

Many underwater missions depend on observations made directly by the diver.

In a scientific survey, this may include:
- species sightings;
- organism counts;
- coral condition;
- bleaching;
- environmental observations.

In an infrastructure inspection, it may include:
- corrosion;
- coating damage;
- marine growth;
- weld condition;
- structural anomalies.

In an environmental survey, it may include:
- debris type;
- estimated quantity;
- entanglement;
- hazardous material;
- location.

The information is most useful when it is captured together with its operational context, such as the current marker, transect, depth and time.
However, manually recording these observations underwater can interrupt the task itself. If observations are instead reconstructed later, some contextual detail may be lost or require additional effort to recover.

#### 3. Mission state is distributed across several pieces of information

A diver does not only need to record observations. They also need to keep track of:

- the current mission objective;
- the active task;
- completed and remaining tasks;
- the current transect and marker;
- communication with the surface team;
- observations that have already been recorded.

These pieces of information are related, but conventional workflows may treat them separately.

For example, reaching marker C2, recording corrosion at C2 and completing the inspection task at C2 are three different events. A useful mission assistant must understand that distinction and update only the appropriate part of the mission state.

#### 4. Diver-to-surface communication adds another interaction layer

The diver may also need to communicate with surface control throughout the mission.

Examples include:

"Visibility has dropped."

"I need five more minutes."

"Do you want a closer inspection of this joint?"

"I have reached marker C2."

The surface team may then respond with new instructions or information.

This creates a two-way communication loop that must coexist with observation logging, task tracking and position awareness. A system that only transcribes speech is therefore not enough. It must understand whether the diver is recording an observation, updating their position, completing a task, sending a message or asking surface a question.

#### 5. Underwater speech is not always clean or perfectly structured

Natural operational speech often contains hesitation, corrections, incomplete phrases and restarts.

For example:

"Log three... actually, two lionfish."

"I'm heading to C4... wait, I've reached C4 now."

"Tell surface visibility is... uh... visibility has dropped significantly."

These utterances contain meaningful corrections that should be resolved before any state is modified.

The system must also deal with mission-specific vocabulary such as species names, structural terminology, survey markers and environmental terms.

A general-purpose transcription system may not have enough context to consistently recognise terms such as "Pterois volitans", "protective coating", "monofilament" or mission markers like "C2" and "D3".

#### 6. Different underwater missions require different operational context

A single fixed vocabulary is not enough.

A reef biodiversity survey may use terms related to species and coral condition.

An infrastructure inspection may focus on corrosion, coatings, welds and structural components.

A marine-debris survey may involve fishing gear, monofilament, entanglement and hazardous debris.

The same voice interface therefore needs to adapt not only its mission instructions, but also the vocabulary and context used by the speech-recognition layer.

#### 7. Generic voice assistants are not designed for structured mission operations

A conversational assistant can answer questions, but an operational assistant needs to do more.

It must distinguish between statements such as:

"I need to move to C4."
and
"I've reached C4."

The first expresses an intended destination.

The second confirms a current position.

Similarly:

"Inspect support joint C2."
does not mean the task is complete.

"Inspection of C2 is complete."
does.

These distinctions matter because the assistant is not merely generating text. It is modifying structured mission state.

#### 8. The core problem

The problem is therefore not simply speech recognition underwater.

The broader challenge is enabling a diver to interact with a mission system naturally, without interrupting the work they are performing.

Such a system needs to convert spoken language into reliable operational actions while maintaining context across:

- mission tasks;
- diver position;
- structured observations;
- corrections;
- diver-to-surface communication;
- surface-to-diver communication.

The interface should reduce interaction overhead rather than create another system the diver has to manage.

## Solution

Dive Copilot is a voice-first AI mission assistant designed to support divers during professional underwater operations.

Instead of requiring the diver to interact with menus, forms or handheld interfaces, Dive Copilot allows mission information to be accessed and updated through natural speech. The diver can ask about the current task, report observations, update their confirmed position, mark mission tasks as complete, communicate with the surface team and retrieve surface responses while continuing the underwater activity.

The system is designed around the idea that underwater voice interaction should not behave like a conventional chatbot. Dive Copilot maintains a structured representation of the active mission and uses the diver's speech to trigger specific operational actions.

For example:

- "I've reached marker C2." updates the diver's confirmed position.
- "Record moderate corrosion on the lower weld." creates a structured observation.
- "Inspection of C2 is complete." marks the corresponding mission task as completed.
- "Tell surface visibility has dropped." sends a message to the surface team.
- "Ask surface whether they need a closer inspection." creates a question for surface control.
- "Anything back from surface?" retrieves the latest surface response.

These actions are deliberately separated. Mentioning a marker does not automatically change the diver's position, discussing a task does not mark it as complete, and reporting an observation does not modify mission progress unless the diver explicitly indicates that the task itself is finished. This separation allows Dive Copilot to maintain mission state rather than simply reacting conversationally to individual sentences.

### Mission-aware voice interaction

Dive Copilot adapts to the mission selected before the dive.

The current prototype includes three simulated mission scenarios:

- Reef Biodiversity Survey;
- Underwater Infrastructure Inspection;
- Marine Debris Survey.

Each mission defines its own objectives, tasks, starting position, terminology and simulated operational context.

The speech-recognition context can also adapt to the selected mission. A reef survey may prioritise vocabulary such as `Pterois volitans`, coral bleaching and reef transects, while an infrastructure inspection may prioritise terms such as corrosion, support joint, weld and protective coating. A marine-debris mission uses terminology such as monofilament, fishing nets and entanglement.

This allows one voice agent to support different operational environments without requiring a separate assistant for every mission type.

### Structured mission actions

Dive Copilot connects natural speech to a set of structured tools rather than treating every interaction as free-form conversation.

The agent can:

- retrieve the active mission;
- retrieve the current dive state;
- update the diver's confirmed marker or transect;
- record structured observations;
- retrieve previously logged observations;
- correct existing observations;
- complete mission tasks;
- send messages to surface control;
- ask questions to surface control;
- retrieve replies from surface.

The backend maintains the mission state throughout the simulation. Observations are automatically associated with contextual information such as timestamp, marker, transect and simulated depth.

This means a spoken report can become structured mission data immediately rather than remaining only as a transcript.

### Handling natural operational speech

Operational speech is rarely perfectly structured. Divers may hesitate, restart sentences or correct themselves.

Dive Copilot is therefore designed to resolve the final intended meaning before changing stored state.

For example:

"Log three... actually, two lionfish."

should create one observation with a count of two, rather than first recording three and then creating a second correction.

Similarly:

"I'm heading to C4."

does not mean the diver is currently at C4.

Only a statement such as:

"I've reached C4."

updates the confirmed mission position.

The agent also supports interruption and barge-in, allowing the diver to interrupt a spoken response rather than waiting for the assistant to finish.

### Diver and surface interfaces

The prototype represents both sides of the mission.

The diver interface presents a compact heads-up-style view containing information such as:

- current task;
- mission progress;
- current marker and transect;
- simulated depth;
- dive time;
- voice-agent state;
- surface-link status.

A separate Surface Control interface provides visibility into:

- active mission state;
- mission progress;
- observations;
- diver-to-surface communication;
- surface replies;
- mission activity and agent actions.

This makes the system useful not only as a conversational assistant but also as a shared operational interface between the diver and the surface team.

### Focus of the prototype

The current system is a simulated proof of concept. Mission telemetry, depth and underwater position are simulated, and the prototype has not yet been integrated with physical diving hardware or subsea communication equipment.

The purpose of the prototype is to demonstrate the interaction model: how real-time voice AI can act as a mission-aware interface between a diver, structured mission data and a surface team.

Dive Copilot is therefore not intended to replace a dive computer, certified diving procedures or qualified surface personnel. Its role is to reduce interaction overhead around mission execution, documentation and communication.

## Key Features

## How It Works

## Application of Technology

## Business Value

Dive Copilot is designed for professional underwater operations where voice communication is already common, but mission information is still fragmented across spoken communication, manual notes, task checklists and separate reporting systems.

Its value is not simply that a diver can speak to an AI assistant. The stronger value is that spoken interaction can be converted directly into structured mission data while the diver continues working.

### Reducing manual documentation

Underwater inspections, scientific surveys and environmental monitoring often require divers to report observations such as species counts, corrosion, coating damage, debris, structural anomalies or changing environmental conditions.

These observations may otherwise need to be written down by a surface operator, transcribed later, or reconstructed during post-dive reporting.

Dive Copilot can turn a spoken statement such as:

> "Record moderate corrosion on the lower weld at C2."

into a structured observation associated with mission context such as:

- current marker;
- transect;
- depth;
- timestamp;
- active mission;
- observation category.

This creates the possibility of reducing duplicated documentation work and shortening the path from underwater observation to usable mission data.

### Improving mission traceability

Dive Copilot maintains structured state throughout the mission rather than storing only a conversation transcript.

The system can track:

- current mission and task;
- completed and remaining tasks;
- confirmed diver position;
- recorded observations;
- observation corrections;
- diver-to-surface messages;
- surface-to-diver replies.

This creates a clearer operational record of what happened during a mission, where it happened and when it happened.

For inspection, research and environmental work, this kind of traceability can make post-mission review and reporting more consistent.

### Reducing interaction overhead

Professional divers often work in environments where their hands and attention are already occupied by tools, samples, inspection equipment, navigation and the surrounding environment.

A voice-first interface allows the diver to interact with the mission system without navigating menus or manually entering information.

The goal is not to replace the diver's existing workflow, but to reduce the amount of attention required to document and manage it.

### Supporting faster diver-to-surface coordination

Dive Copilot also acts as an interface between the diver and surface control.

The diver can:

- send operational updates;
- ask questions;
- retrieve surface responses;
- report changing conditions;
- communicate mission progress.

This creates a shared operational workflow instead of treating documentation, mission tracking and communication as separate activities.

### Adapting to different operational domains

The same Dive Copilot architecture can support different underwater mission types by changing mission configuration, task definitions and speech-recognition context.

The current prototype demonstrates this with:

- reef biodiversity surveys;
- underwater infrastructure inspections;
- marine debris surveys.

This makes the concept relevant beyond a single diving use case.

Potential application areas include:

- offshore infrastructure inspection;
- offshore wind operations and maintenance;
- subsea decommissioning;
- ports and civil infrastructure inspection;
- scientific diving;
- environmental monitoring;
- aquaculture;
- marine engineering and maintenance.

### Potential customers

The primary users are divers and surface operators, but the likely buyers are organisations responsible for underwater operations and the data produced by them.

Potential customers include:

- commercial diving contractors;
- offshore operators;
- marine engineering companies;
- infrastructure owners;
- research institutes;
- environmental consultancies;
- government and public-sector marine organisations.

For these organisations, the value is less about the conversational interface itself and more about the operational outcomes it can support:

- less manual transcription;
- more structured mission records;
- faster reporting workflows;
- improved traceability;
- easier communication between diver and surface team;
- better integration between underwater work and digital systems.

### Commercial direction

A realistic first market for Dive Copilot would be professional underwater inspection teams that already rely on diver-to-surface voice communication.

In these environments, Dive Copilot would not require a completely new interaction model. Instead, it could add an intelligent software layer to an existing voice-based workflow.

Over time, the product could evolve from a standalone mission assistant into an integration layer for existing operational systems, including:

- inspection databases;
- asset-management platforms;
- work-order systems;
- digital twins;
- real telemetry;
- sensor data;
- camera feeds;
- dive-control systems.

The longer-term opportunity is therefore not only to provide a voice assistant for divers, but to create a natural-language interface between underwater personnel and the wider digital systems used to manage marine operations.

| Market | Typical use | Buyer |
|---|---|---|
| **Commercial underwater inspection** | corrosion, welds, coating damage, structural anomalies | diving contractors, marine engineering firms, asset owners |
| **Offshore wind O&M** | foundations, cables, substations, underwater assets | wind-farm operators, O&M contractors |
| **Oil & gas / decommissioning** | inspection, repair, removal, condition reporting | offshore operators, subsea contractors |
| **Ports & civil infrastructure** | bridges, quay walls, dams, pipelines | ports, municipalities, engineering contractors |
| **Scientific diving** | biodiversity, coral, habitat surveys | universities, research institutes |
| **Environmental monitoring** | marine debris, pollution, ecological surveys | environmental consultancies, government agencies |
| **Aquaculture** | cages, nets, infrastructure inspection | fish-farm operators |



## Originality

## Demo Scenarios
### Reef Biodiversity Survey
### Underwater Infrastructure Inspection
### Marine Debris Survey

## Technology Stack

## GitHub Repository

## Application URL

## Video Presentation

## Slide Presentation