"""Offline behavioral test for the concept-first thought-generation façade."""

from __future__ import annotations

import json
from pprint import pprint

from bot0_thought_graph import ThoughtGraphEngine

try:
    from examples.support import FakeProvider
except ModuleNotFoundError:  # Supports direct execution from the repository root.
    from support import FakeProvider


HORIZONTAL = (
    '{"idea":"systems","thoughts":['
    '{"thought":"hardware","description":"Physical design"},'
    '{"thought":"software","description":"Program logic"}]}'
)
VERTICAL = (
    '{"idea":"systems","thought":"hardware","sub_thoughts":['
    '{"name":"requirements","description":"Define needs"},'
    '{"name":"design","description":"Choose structure"}]}'
)


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_graph(node, indent: int = 0) -> None:
    prefix = "  " * indent
    print(f"{prefix}- {node.name}")

    if node.description:
        print(f"{prefix}  Description: {node.description}")

    for child in node.children:
        print_graph(child, indent + 1)


def main() -> None:
    # One response is needed for each operation below. The final two vertical
    # responses are consumed while expanding the two first-level graph nodes.
    provider = FakeProvider([HORIZONTAL, VERTICAL, HORIZONTAL, HORIZONTAL, VERTICAL, VERTICAL])
    engine = ThoughtGraphEngine(provider, model="example-model")
    concept = "systems"

    print_section("1. HORIZONTAL EXPANSION")
    subtopics = engine.generate_subtopics(concept, max_subtopics=2)
    pprint(subtopics)

    print_section("2. VERTICAL EXPANSION")
    selected_subtopic = subtopics[0]
    details = engine.expand_subtopic(
        concept=concept,
        subtopic=selected_subtopic,
        max_details=2,
    )
    print(f"Parent: {selected_subtopic}")
    pprint(details)

    print_section("3. STRUCTURED THOUGHT ARRAY")
    thought_array = engine.generate_array_of_thoughts(concept, max_subtopics=2)
    print(thought_array.model_dump_json(indent=2))

    print_section("4. DEPTH-2 THOUGHT GRAPH")
    graph = engine.generate_thought_graph(concept, depth=2, breadth=2)
    print_graph(graph.root)
    print(json.dumps(graph.model_dump(), indent=2))


if __name__ == "__main__":
    main()
