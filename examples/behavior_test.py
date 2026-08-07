"""Live smoke test for the concept-first thought-generation façade."""

from __future__ import annotations

import os

from bot0_thought_graph import ThoughtGraphEngine
from bot0_thought_graph.providers import OpenAIProvider


CONCEPT = "Clinical research recruitment"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini-2025-08-07")


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def choose_vertical_parent(subtopics: list[str]) -> str:
    """Pick a direct-child parent deterministically without another model call."""
    if "Participant eligibility" in subtopics:
        return "Participant eligibility"

    ordered_keywords = (
        "eligibility",
        "participant",
        "screening",
        "recruitment",
        "enrollment",
        "consent",
    )
    lowered = [item.lower() for item in subtopics]
    for keyword in ordered_keywords:
        for original, normalized in zip(subtopics, lowered, strict=True):
            if keyword in normalized:
                return original

    return subtopics[0]


def main() -> None:
    provider = OpenAIProvider()
    engine = ThoughtGraphEngine(provider, model=MODEL)

    print_section("HORIZONTAL RESULT")
    print(f"Concept: {CONCEPT}")
    print(f"Model: {MODEL}")

    array = engine.generate_array_of_thoughts(CONCEPT, max_subtopics=6)
    for index, thought in enumerate(array.thoughts, start=1):
        print(f"{index}. {thought.name}")
        print(f"   Description: {thought.description}")

    selected_parent = choose_vertical_parent([thought.name for thought in array.thoughts])

    print_section("VERTICAL DIRECT-CHILD RESULT")
    print(f"Concept: {CONCEPT}")
    print(f"Selected parent: {selected_parent}")

    children = engine.expand_subtopic(
        concept=CONCEPT,
        subtopic=selected_parent,
        max_details=6,
    )
    for index, child in enumerate(children, start=1):
        print(f"{index}. {child}")


if __name__ == "__main__":
    main()
