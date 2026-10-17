                         CADDY-REIMAGINED
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│                         DIVER SIDE                                │
│                                                                   │
│  Wearables / Sensors                     Diver Voice              │
│         │                                     │                   │
│         ▼                                     ▼                   │
│  Preprocessing                        Audio Interface             │
│         │                                     │                   │
│  State Estimation                             │                   │
│         │                                     │                   │
│  Alarm Engine                                 │                   │
│         │                                     │                   │
│  DiverSafetyPacket                            │                   │
│         │                                     │                   │
└─────────┼─────────────────────────────────────┼───────────────────┘
          │                                     │
          │ structured telemetry                │ voice comms
          ▼                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION LAYER                            │
│                                                                   │
│      Acoustic Link / Diver Comms / Surface Gateway                │
│                                                                   │
└─────────┬─────────────────────────────────────┬───────────────────┘
          │                                     │
          ▼                                     ▼
┌───────────────────────┐             ┌─────────────────────────────┐
│ Diver Safety Pipeline │             │     VOICE INTERACTION       │
│                       │             │          LAYER              │
│ alarms                │             │                             │
│ state                 │             │ Voice Gateway               │
│ telemetry             │             │ STT                         │
└───────────┬───────────┘             │ Voice Agent                 │
            │                         │ Intent / Tool Adapter       │
            │                         │ TTS                         │
            │                         └──────────────┬──────────────┘
            │                                        │
            │                              structured request
            │                                        │
            ▼                                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                       MISSION BACKEND                             │
│                                                                   │
│  MissionService                                                   │
│  Mission State                                                    │
│  Tasks                                                            │
│  Observations                                                     │
│  Position                                                         │
│  Events                                                           │
│  Communications                                                   │
│                                                                   │
│                 ┌─────────────────────────┐                       │
│                 │ Command / Policy Gate   │                       │
│                 │                         │                       │
│                 │ validate intent         │                       │
│                 │ check mission state     │                       │
│                 │ check safety state      │                       │
│                 │ authorize action        │                       │
│                 └───────────┬─────────────┘                       │
│                             │                                     │
└─────────────────────────────┼─────────────────────────────────────┘
                              │
                    high-level approved action
                              │
                              ▼
               ┌─────────────────────────────┐
               │ RobotSystem / Planner       │
               │                             │
               │ behavior planning           │
               │ navigation requests         │
               │ diver assistance            │
               └─────────────┬───────────────┘
                             │
                             ▼
               ┌─────────────────────────────┐
               │ C++ Vehicle Control Core    │
               │                             │
               │ motion control              │
               │ thruster allocation         │
               │ vehicle dynamics            │
               └─────────────────────────────┘

                              │
                              ▼
               ┌─────────────────────────────┐
               │ Surface Operations Console  │
               │                             │
               │ telemetry                   │
               │ voice events                │
               │ mission state               │
               │ robot state                 │
               │ alarms                      │
               │ communications              │
               └─────────────────────────────┘