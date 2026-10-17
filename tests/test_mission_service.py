import tempfile
import unittest
from pathlib import Path

from backend.domain.models import EventType
from backend.persistence.repository import MissionRepository
from backend.services.mission_service import MissionService


class MissionServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = MissionRepository("sqlite:///:memory:")
        self.service = MissionService(
            "infrastructure-inspection",
            repository=self.repository,
        )

    def event_types(self):
        return [event["type"] for event in self.service.events()]

    def test_reset_starts_a_fresh_mission_event_stream(self):
        events = self.service.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], EventType.MISSION_STARTED.value)
        self.assertEqual(events[0]["payload"]["marker"], "C1")

    def test_observation_is_structured_and_emits_event(self):
        observation = self.service.log_observation(
            category="structure",
            description="Moderate corrosion at support joint C2",
            count=None,
        )

        self.assertEqual(observation.id, 1)
        self.assertEqual(observation.marker, "C1")
        self.assertIn(EventType.OBSERVATION_CREATED.value, self.event_types())

    def test_observation_correction_preserves_history(self):
        observation = self.service.log_observation(
            category="structure",
            description="Moderate corrosion",
            count=None,
        )

        status, corrected, error = self.service.correct_observation(
            observation_id=observation.id,
            changes={"description": "Slight corrosion"},
        )

        self.assertEqual(status, "corrected")
        self.assertIsNone(error)
        self.assertIsNotNone(corrected)
        self.assertEqual(corrected.description, "Slight corrosion")
        self.assertEqual(len(corrected.correction_history), 1)
        self.assertEqual(
            corrected.correction_history[0].previous["description"],
            "Moderate corrosion",
        )
        self.assertIn(EventType.OBSERVATION_CORRECTED.value, self.event_types())

    def test_task_completion_is_idempotent_and_event_is_not_duplicated(self):
        first = self.service.complete_task("task-1")
        second = self.service.complete_task("task-1")

        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["status"], "already_completed")
        task_events = [
            event
            for event in self.service.events()
            if event["type"] == EventType.TASK_COMPLETED.value
        ]
        self.assertEqual(len(task_events), 1)

    def test_confirmed_position_change_emits_event(self):
        position = self.service.update_position(transect=None, marker="C2")

        self.assertEqual(position.marker, "C2")
        events = self.service.events()
        self.assertEqual(events[-1]["type"], EventType.POSITION_CONFIRMED.value)
        self.assertEqual(events[-1]["payload"]["position"]["marker"], "C2")

    def test_same_position_does_not_create_duplicate_event(self):
        before = len(self.service.events())
        self.service.update_position(transect="C", marker="C1")
        after = len(self.service.events())
        self.assertEqual(before, after)

    def test_surface_question_and_reply_are_both_in_timeline(self):
        question = self.service.ask_surface(
            question="Proceed with closer inspection?",
            priority="routine",
        )
        self.service.send_surface_reply(
            message="Proceed with the inspection.",
            in_reply_to=question.id,
        )

        self.assertEqual(self.service.surface_messages[0].status, "answered")
        self.assertIn(EventType.SURFACE_QUESTION_SENT.value, self.event_types())
        self.assertIn(EventType.SURFACE_REPLY_RECEIVED.value, self.event_types())

    def test_selecting_new_mission_resets_state_and_event_ids(self):
        self.service.log_observation(
            category="structure",
            description="Corrosion",
            count=None,
        )
        self.service.reset("reef-survey")

        self.assertEqual(self.service.active_mission_key, "reef-survey")
        self.assertEqual(self.service.list_observations(), [])
        events = self.service.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], 1)
        self.assertEqual(events[0]["type"], EventType.MISSION_STARTED.value)

        sessions = self.repository.list_sessions()
        self.assertEqual(len(sessions), 2)
        self.assertFalse(sessions[0]["active"])
        self.assertTrue(sessions[1]["active"])


class MissionPersistenceTests(unittest.TestCase):
    def test_active_mission_is_restored_after_service_restart(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "mission.db"
            database_url = f"sqlite:///{db_path}"

            first_repository = MissionRepository(database_url)
            first = MissionService(
                "infrastructure-inspection",
                repository=first_repository,
            )
            first.update_position(transect=None, marker="C2")
            observation = first.log_observation(
                category="structure",
                description="Moderate corrosion at support joint C2",
                count=None,
            )
            first.correct_observation(
                observation_id=observation.id,
                changes={"description": "Slight corrosion at support joint C2"},
            )
            first.complete_task("task-1")
            question = first.ask_surface(
                question="Proceed with closer inspection?",
                priority="routine",
            )
            first.send_surface_reply(
                message="Proceed with the inspection.",
                in_reply_to=question.id,
            )
            expected_event_count = len(first.events())

            # Simulate a new application process with a new repository/engine.
            second_repository = MissionRepository(database_url)
            restored = MissionService(
                "reef-survey",
                repository=second_repository,
            )

            self.assertEqual(restored.active_mission_key, "infrastructure-inspection")
            self.assertEqual(restored.position.marker, "C2")
            self.assertTrue(restored.mission.tasks[0].completed)
            self.assertEqual(restored.current_task().id, "task-2")

            observations = restored.list_observations()
            self.assertEqual(len(observations), 1)
            self.assertEqual(
                observations[0]["description"],
                "Slight corrosion at support joint C2",
            )
            self.assertEqual(len(observations[0]["correction_history"]), 1)

            self.assertEqual(restored.surface_messages[0].status, "answered")
            self.assertEqual(len(restored.surface_replies), 1)
            self.assertEqual(len(restored.events()), expected_event_count)

    def test_event_sequence_continues_after_restart(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "events.db"
            database_url = f"sqlite:///{db_path}"

            first = MissionService(
                "infrastructure-inspection",
                repository=MissionRepository(database_url),
            )
            first.update_position(transect=None, marker="C2")
            self.assertEqual(first.events()[-1]["id"], 2)

            restored = MissionService(
                "reef-survey",
                repository=MissionRepository(database_url),
            )
            restored.log_observation(
                category="structure",
                description="Minor marine growth",
                count=None,
            )

            self.assertEqual(restored.events()[-1]["id"], 3)
            self.assertEqual(
                restored.events()[-1]["type"],
                EventType.OBSERVATION_CREATED.value,
            )


if __name__ == "__main__":
    unittest.main()
