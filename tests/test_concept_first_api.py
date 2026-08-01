from dataclasses import dataclass

import pytest

from bot0_thought_graph import ThoughtArray, ThoughtGraph, ThoughtGraphEngine
from bot0_thought_graph.providers import GenerationRequest, GenerationResult


@dataclass
class FakeProvider:
    responses: list[str]

    def __post_init__(self):
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        return GenerationResult(self.responses.pop(0), "fake", request.model)


HORIZONTAL = (
    '{"idea":"Clinical research recruitment","thoughts":['
    '{"thought":"Participant eligibility","description":"Who may participate"},'
    '{"thought":"Recruitment strategy","description":"How participants are reached"},'
    '{"thought":"Screening workflow","description":"How candidates are assessed"}'
    ']}'
)
VERTICAL = (
    '{"idea":"Clinical research recruitment","thought":"Participant eligibility",'
    '"sub_thoughts":['
    '{"name":"Inclusion criteria","description":"Required characteristics"},'
    '{"name":"Exclusion criteria","description":"Disqualifying characteristics"},'
    '{"name":"Safety screening","description":"Initial safety checks"}'
    ']}'
)


def test_convenience_methods_translate_horizontal_and_vertical_requests():
    provider = FakeProvider([HORIZONTAL, VERTICAL])
    engine = ThoughtGraphEngine(provider, model="fake-model")

    assert engine.generate_subtopics("Clinical research recruitment", max_subtopics=3) == [
        "Participant eligibility",
        "Recruitment strategy",
        "Screening workflow",
    ]
    assert engine.expand_subtopic(
        "Clinical research recruitment", "Participant eligibility", max_details=3
    ) == ["Inclusion criteria", "Exclusion criteria", "Safety screening"]

    horizontal_request, vertical_request = provider.requests
    assert horizontal_request.model == "fake-model"
    assert horizontal_request.max_tokens == 1056
    assert "horizontal set of major subtopics" in horizontal_request.prompt
    assert vertical_request.model == "fake-model"
    assert vertical_request.prompt.startswith("\nYou are an expert at vertically expanding")
    assert "direct child details" in vertical_request.prompt


def test_structured_array_and_graph_are_public_typed_results_without_persistence(tmp_path):
    provider = FakeProvider([HORIZONTAL])
    engine = ThoughtGraphEngine(provider)
    array = engine.generate_array_of_thoughts("Clinical research recruitment", max_subtopics=2)

    assert isinstance(array, ThoughtArray)
    assert array.concept == "Clinical research recruitment"
    assert [thought.name for thought in array.thoughts] == [
        "Participant eligibility",
        "Recruitment strategy",
        "Screening workflow",
    ][:2]
    assert list(tmp_path.iterdir()) == []

    provider = FakeProvider([HORIZONTAL, VERTICAL, VERTICAL, VERTICAL])
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment", depth=2, breadth=2
    )
    assert isinstance(graph, ThoughtGraph)
    assert graph.concept == "Clinical research recruitment"
    assert graph.root.name == graph.concept
    assert len(graph.root.children) == 2
    assert all(len(child.children) == 2 for child in graph.root.children)
    assert len(provider.requests) == 3  # one horizontal call plus one per branch
    assert all("direct child details" in request.prompt for request in provider.requests[1:])


def test_graph_depth_one_has_no_vertical_calls_and_breadth_is_enforced():
    provider = FakeProvider([HORIZONTAL])
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment", depth=1, breadth=1
    )
    assert len(graph.root.children) == 1
    assert graph.root.children[0].children == []
    assert len(provider.requests) == 1


@pytest.mark.parametrize(
    "call",
    [
        lambda engine: engine.generate_subtopics(" "),
        lambda engine: engine.expand_subtopic("concept", "\t"),
        lambda engine: engine.generate_subtopics("concept", max_subtopics=0),
        lambda engine: engine.expand_subtopic("concept", "topic", max_details=-1),
        lambda engine: engine.generate_thought_graph("concept", depth=0),
        lambda engine: engine.generate_thought_graph("concept", breadth=0),
        lambda engine: engine.generate_thought_graph("concept", depth=4),
    ],
)
def test_concept_first_validation_rejects_invalid_input(call):
    with pytest.raises(ValueError):
        call(ThoughtGraphEngine(FakeProvider([])))
