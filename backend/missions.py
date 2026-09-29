from copy import deepcopy

MISSION_TEMPLATES = {
    "reef-survey": {
        "mission_id": "reef-survey-001",
        "name": "Reef Biodiversity Survey",
        "description": ("Conduct a scientific biodiversity survey along reef transect B, "
                        "recording fish populations and visible coral bleaching."),
        "site": "Reef Sector B",
        "diver": "Diver 1",
        "transect": "B",
        "start_marker": "B1",
        "status": "active",
        "simulation": {
            "summary": "Scientific reef monitoring and biodiversity survey.",
            "depth_m": 14.2},
        "tasks": [{
            "id": "task-1",
            "description": "Survey fish population along transect B",
            "completed": False}, {
            "id": "task-2",
            "description": "Record visible coral bleaching",
            "completed": False}, {
            "id": "task-3",
            "description": "Complete observations at marker B4",
            "completed": False}]},
    "infrastructure-inspection": {
        "mission_id": "infrastructure-inspection-001",
        "name": "Underwater Infrastructure Inspection",
        "description": ("Inspect an underwater structure for visible corrosion, coating "
                        "damage and structural anomalies."),
        "site": "Offshore Structure A",
        "diver": "Diver 1",
        "transect": "C",
        "start_marker": "C1",
        "status": "active",
        "simulation": {
            "summary": "Inspection of submerged industrial infrastructure.",
            "depth_m": 18.6, },
        "tasks": [{
            "id": "task-1",
            "description": "Inspect support joint C2 for visible damage",
            "completed": False, }, {
            "id": "task-2",
            "description": "Record corrosion or marine growth along section C",
            "completed": False, }, {
            "id": "task-3",
            "description": "Inspect protective coating near marker C4",
            "completed": False, }, {
            "id": "task-4",
            "description": "Report significant structural anomalies to surface control",
            "completed": False, }, ], },

    "marine-debris": {
        "mission_id": "marine-debris-001",
        "name": "Marine Debris Survey",
        "description": ("Survey coastal sector D for marine debris, documenting debris "
                        "type, estimated quantity and location."),
        "site": "Coastal Survey Sector D",
        "diver": "Diver 1",
        "transect": "D",
        "start_marker": "D1",
        "status": "active",
        "simulation": {
            "summary": "Marine debris identification and environmental survey.",
            "depth_m": 11.8, },
        "tasks": [{
            "id": "task-1",
            "description": "Survey marine debris along transect D",
            "completed": False, }, {
            "id": "task-2",
            "description": "Record debris type and estimated quantity",
            "completed": False}, {
            "id": "task-3",
            "description": "Inspect marker D3 for entangled fishing gear",
            "completed": False}, {
            "id": "task-4",
            "description": "Report hazardous debris to surface control",
            "completed": False}]}}

MISSION_SPEECH_CONTEXT = {
    "reef-survey": {
        "keyterms": ["Dive Copilot", "reef", "reef survey", "biodiversity", "transect", "marker", "surface", "lionfish",
            "Pterois volitans", "Acropora", "Porites", "coral bleaching", "bleaching", "fish population", "substrate", "B1",
            "B2", "B3", "B4", "B5", ],
        "transcription_prompt": ("A professional diver is conducting a reef biodiversity survey. "
                                 "The diver may report fish species, organism counts, coral condition, "
                                 "bleaching, reef substrate, transect identifiers, marker identifiers, "
                                 "depth, observations, mission tasks, and messages to surface control."), },

    "infrastructure-inspection": {
        "keyterms": ["Dive Copilot", "infrastructure inspection", "Offshore Structure A", "transect", "marker", "surface",
            "support joint", "corrosion", "coating", "protective coating", "marine growth", "structural anomaly",
            "structural anomalies", "weld", "lower weld", "C1", "C2", "C3", "C4", "C5", ],
        "transcription_prompt": ("A professional diver is conducting an underwater infrastructure "
                                 "inspection at Offshore Structure A. The diver may report corrosion, "
                                 "coating damage, marine growth, weld condition, support joints, "
                                 "structural anomalies, transect identifiers, marker identifiers, "
                                 "mission tasks, and communication with surface control."), },

    "marine-debris": {
        "keyterms": ["Dive Copilot", "marine debris", "debris survey", "Coastal Survey Sector D", "transect", "marker",
            "surface", "fishing net", "fishing nets", "fishing line", "monofilament", "entanglement",
            "entangled fishing gear", "plastic debris", "hazardous debris", "recovery", "D1", "D2", "D3", "D4", "D5", ],
        "transcription_prompt": ("A professional diver is conducting a marine debris survey. "
                                 "The diver may report fishing nets, fishing line, monofilament, "
                                 "entangled gear, plastic debris, hazardous debris, quantities, "
                                 "transect identifiers, marker identifiers, environmental observations, "
                                 "mission tasks, and communication with surface control."), }, }

DEFAULT_MISSION_KEY = "reef-survey"


def get_mission_speech_context(mission_key: str) -> dict:
    if mission_key not in MISSION_SPEECH_CONTEXT:
        raise KeyError(f"Unknown mission: {mission_key}")

    return deepcopy(MISSION_SPEECH_CONTEXT[mission_key])


def build_mission(mission_key: str) -> dict:
    """
    Return a fresh copy of a mission.

    A deepcopy is important because task completion modifies
    mission state during the simulation.
    """
    if mission_key not in MISSION_TEMPLATES:
        raise KeyError(f"Unknown mission: {mission_key}")

    return deepcopy(MISSION_TEMPLATES[mission_key])


def list_missions() -> list[dict]:
    """
    Return the lightweight mission metadata used by the UI.
    """
    missions = []

    for key, mission in MISSION_TEMPLATES.items():
        missions.append({
            "id": key,
            "name": mission["name"],
            "description": mission["description"],
            "site": mission["site"],
            "summary": mission["simulation"]["summary"],
            "task_count": len(mission["tasks"])})

    return missions
