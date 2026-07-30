"""Explicit thought-graph traversal state transitions."""

from bot0_thought_graph.models import IndexedIdeaJSONModel


def has_current_sub_thought(graph: IndexedIdeaJSONModel, thought_index: int, sub_thought_index: int) -> bool:
    if not graph.thoughts or thought_index >= len(graph.thoughts):
        return False
    sub_thoughts = graph.thoughts[thought_index].sub_thoughts or []
    return sub_thought_index < len(sub_thoughts)


def next_location(graph: IndexedIdeaJSONModel, thought_index: int, sub_thought_index: int) -> tuple[int, int] | None:
    if not graph.thoughts:
        return None
    current = graph.thoughts[thought_index]
    if sub_thought_index + 1 < len(current.sub_thoughts or []):
        return thought_index, sub_thought_index + 1
    next_thought = thought_index + 1
    if next_thought < len(graph.thoughts) and (graph.thoughts[next_thought].sub_thoughts or []):
        return next_thought, 0
    return None
