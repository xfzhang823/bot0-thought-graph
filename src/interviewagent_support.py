"""Shared interview state and question-loading helpers.

This module intentionally avoids FastAPI so that state management and
question loading can be imported without pulling in the web app.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import logging_config

from bot0_thought_graph.thought_generation import IndexedThoughtReader
from project_config import INTERVIEW_STATES_FILE
from utils.generic_utils import read_from_json_file

logger = logging.getLogger(__name__)


class StateManager:
    """Persist and mutate per-user interview progress."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else INTERVIEW_STATES_FILE
        self.states = self._load_states()

    def _load_states(self):
        try:
            with self.storage_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def persist(self):
        """Persist states to the configured file."""
        with self.storage_path.open("w", encoding="utf-8") as handle:
            json.dump(self.states, handle)

    def get_state(self, user_id: str):
        """Retrieve or initialize a user's state."""
        if user_id not in self.states:
            self.states[user_id] = {
                "thought_index": 0,
                "sub_thought_index": 0,
                "current_question": None,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            self.persist()
        return self.states[user_id]

    def update_state(self, user_id: str, **updates):
        """Update a user's state and persist the change."""
        state = self.get_state(user_id)
        state.update(updates)
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.persist()

    def reset_state(self, user_id: str):
        """Delete a user's state and persist the change."""
        if user_id in self.states:
            del self.states[user_id]
        self.persist()


class QuestionLoader:
    """Load indexed thought data and step through questions in source order."""

    def __init__(self, data_file: Path | str):
        self.data_source = self._load_data(data_file)

    def _load_data(self, data_file: Path | str):
        reader = IndexedThoughtReader(read_from_json_file(data_file))
        output_data = reader.dump_all()
        logger.info("idea model output: %s", output_data)
        return output_data

    def get_next_question(self, user_id: str, state_manager: StateManager):
        """Fetch the next question based on the user's current state."""
        state = state_manager.get_state(user_id)

        try:
            thought = self.data_source["thoughts"][state["thought_index"]]
            sub_thought = thought["sub_thoughts"][state["sub_thought_index"]]

            state_manager.update_state(
                user_id,
                thought_index=state["thought_index"],
                sub_thought_index=state["sub_thought_index"] + 1,
            )

            if state_manager.get_state(user_id)["sub_thought_index"] >= len(
                thought["sub_thoughts"]
            ):
                state_manager.update_state(
                    user_id,
                    thought_index=state["thought_index"] + 1,
                    sub_thought_index=0,
                )

            return {"thought": thought, "sub_thought": sub_thought}
        except IndexError:
            state_manager.reset_state(user_id)
            return {"message": "No more questions available."}
