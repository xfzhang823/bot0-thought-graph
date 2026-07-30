"""In-memory readers for validated thought graphs."""

from collections.abc import Mapping
from typing import Any

from bot0_thought_graph.models import IdeaJSONModel, IndexedIdeaJSONModel

from .validation import validate_idea, validate_indexed_idea


class ThoughtReader:
    """Read an already supplied unindexed model without filesystem access."""

    def __init__(self, data: Mapping[str, Any] | IdeaJSONModel) -> None:
        self.idea_instance = validate_idea(data)

    def get_idea(self) -> str:
        return self.idea_instance.idea

    def get_thoughts(self) -> list[str]:
        return [item.thought for item in self.idea_instance.thoughts or []]

    def get_thoughts_and_descriptions(self) -> list[dict[str, Any]]:
        return [
            {"thought": item.thought, "description": item.description}
            for item in self.idea_instance.thoughts or []
        ]

    def get_sub_thoughts_for_thought(self, thought_name: str) -> list[dict[str, Any]]:
        for thought in self.idea_instance.thoughts or []:
            if thought.thought == thought_name:
                return [
                    {
                        "name": item.name,
                        "description": item.description,
                        "importance": item.importance,
                        "connection_to_next": item.connection_to_next,
                    }
                    for item in thought.sub_thoughts or []
                ]
        return []


class IndexedThoughtReader:
    """Read an already supplied indexed model without filesystem access."""

    def __init__(self, data: Mapping[str, Any] | IndexedIdeaJSONModel) -> None:
        self.idea_instance = validate_indexed_idea(data)

    def get_idea(self) -> str:
        return self.idea_instance.idea

    def get_thoughts(self) -> list[dict[str, Any]]:
        return [
            {"thought_index": item.thought_index, "thought": item.thought}
            for item in self.idea_instance.thoughts or []
        ]

    def get_thoughts_and_descriptions(self) -> list[dict[str, Any]]:
        return [
            {
                "thought_index": item.thought_index,
                "thought": item.thought,
                "description": item.description,
            }
            for item in self.idea_instance.thoughts or []
        ]

    def get_sub_thoughts_for_thought(self, thought_index: int) -> list[dict[str, Any]]:
        for thought in self.idea_instance.thoughts or []:
            if thought.thought_index == thought_index:
                return [
                    {
                        "sub_thought_index": item.sub_thought_index,
                        "name": item.name,
                        "description": item.description,
                        "importance": item.importance,
                        "connection_to_next": item.connection_to_next,
                    }
                    for item in thought.sub_thoughts or []
                ]
        return []

    def dump_all(self) -> dict[str, Any]:
        return self.idea_instance.model_dump()
