import json
import tempfile
import unittest
from pathlib import Path

from interviewagent_support import QuestionLoader, StateManager


MOCK_DATA = {
    "idea": "embedded software development",
    "thoughts": [
        {
            "thought_index": 0,
            "thought": "System Essentials",
            "description": "Focuses on the core operating systems...",
            "sub_thoughts": [
                {
                    "sub_thought_index": 0,
                    "name": "Define System Requirements",
                    "description": "Identify the specific needs...",
                    "importance": "Defining system requirements is crucial...",
                    "connection_to_next": "Knowing the requirements helps...",
                },
                {
                    "sub_thought_index": 1,
                    "name": "Select Appropriate Hardware",
                    "description": "Choose suitable hardware components...",
                    "importance": "Selecting appropriate hardware is essential...",
                    "connection_to_next": "Once the hardware is selected...",
                },
            ],
        }
    ],
}


class TestInterviewAgentSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        base_dir = Path(cls.temp_dir.name)
        cls.mock_json_path = base_dir / "mock_thoughts.json"
        cls.mock_state_path = base_dir / "test_states.json"
        cls.mock_state_path.write_text("{}")
        cls.mock_json_path.write_text(json.dumps(MOCK_DATA))

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_state_manager_round_trip(self):
        state_manager = StateManager(storage_path=str(self.mock_state_path))
        state = state_manager.get_state("user-1")
        self.assertEqual(state["thought_index"], 0)
        self.assertEqual(state["sub_thought_index"], 0)

        state_manager.update_state("user-1", thought_index=1, sub_thought_index=2)
        updated = state_manager.get_state("user-1")
        self.assertEqual(updated["thought_index"], 1)
        self.assertEqual(updated["sub_thought_index"], 2)

        state_manager.reset_state("user-1")
        reset = state_manager.get_state("user-1")
        self.assertEqual(reset["thought_index"], 0)
        self.assertEqual(reset["sub_thought_index"], 0)

    def test_question_loader_steps_through_data(self):
        loader = QuestionLoader(self.mock_json_path)
        state_manager = StateManager(storage_path=str(self.mock_state_path))

        first = loader.get_next_question("user-1", state_manager)
        self.assertEqual(first["sub_thought"]["name"], "Define System Requirements")

        second = loader.get_next_question("user-1", state_manager)
        self.assertEqual(second["sub_thought"]["name"], "Select Appropriate Hardware")

        final = loader.get_next_question("user-1", state_manager)
        self.assertEqual(final["message"], "No more questions available.")


if __name__ == "__main__":
    unittest.main()
