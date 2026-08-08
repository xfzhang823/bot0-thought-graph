from dataclasses import dataclass

import pytest

from bot0_thought_graph import ProgressionType, ThoughtArray, ThoughtGraph, ThoughtGraphEngine
from bot0_thought_graph.providers import GenerationRequest, GenerationResult
from bot0_thought_graph.thought_generation import engine as engine_module


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
    assert "implementation steps" in vertical_request.prompt


def test_engine_accepts_provider_name_through_existing_factory(monkeypatch):
    provider = FakeProvider([])
    seen = {}

    def fake_create_provider(name):
        seen["provider"] = name
        return provider

    monkeypatch.setattr(engine_module, "create_provider", fake_create_provider)
    engine = ThoughtGraphEngine(" DeepSeek ", model="deepseek-v4-flash")

    assert engine.provider is provider
    assert seen["provider"] == "deepseek"
    assert engine.model == "deepseek-v4-flash"


def test_named_provider_uses_factory_default_model_when_model_is_none(monkeypatch):
    provider = FakeProvider([])
    monkeypatch.setattr(engine_module, "create_provider", lambda name: provider)
    monkeypatch.setattr(engine_module, "default_model", lambda name: "provider-default")

    engine = ThoughtGraphEngine("openai", model=None)

    assert engine.provider is provider
    assert engine.model == "provider-default"


def test_injected_provider_object_remains_supported():
    provider = FakeProvider([])
    engine = ThoughtGraphEngine(provider, model="fake-model")

    assert engine.provider is provider
    assert engine.model == "fake-model"


def test_convenience_methods_forward_configured_token_budgets():
    provider = FakeProvider([HORIZONTAL, VERTICAL])
    engine = ThoughtGraphEngine(provider, model="fake-model")

    engine.generate_array_of_thoughts("systems", max_tokens=4096)
    engine.expand_subtopic("systems", "hardware", max_tokens=4096)

    assert [request.max_tokens for request in provider.requests] == [4096, 4096]


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
    assert graph.depth == 2
    assert graph.breadth == 2
    assert graph.root.name == graph.concept
    assert len(graph.root.children) == 2
    assert all(len(child.children) == 2 for child in graph.root.children)
    assert len(provider.requests) == 3  # one horizontal call plus one per branch
    assert all("implementation steps" in request.prompt for request in provider.requests[1:])
    assert all(
        'Progression type: "implementation_steps"' in request.prompt
        for request in provider.requests[1:]
    )
    assert ProgressionType.IMPLEMENTATION_STEPS.value == "implementation_steps"


def test_graph_depth_one_has_no_vertical_calls_and_breadth_is_enforced():
    provider = FakeProvider([HORIZONTAL])
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment", depth=1, breadth=1
    )
    assert len(graph.root.children) == 1
    assert graph.root.children[0].children == []
    assert len(provider.requests) == 1


def test_graph_normalizes_progression_type_and_includes_it_in_vertical_prompts():
    provider = FakeProvider([HORIZONTAL, VERTICAL, VERTICAL, VERTICAL])
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment",
        depth=2,
        breadth=2,
        progression_type="prerequisite_dependency",
    )

    assert isinstance(graph, ThoughtGraph)
    assert all(
        'Progression type: "prerequisite_dependency"' in request.prompt
        for request in provider.requests[1:]
    )
    assert ProgressionType.PREREQUISITE_DEPENDENCY.value == "prerequisite_dependency"


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


def test_named_provider_and_model_validation_are_clear():
    with pytest.raises(ValueError, match="Unsupported provider"):
        ThoughtGraphEngine("unsupported", model="model")
    with pytest.raises(ValueError, match="model must not be empty"):
        ThoughtGraphEngine(FakeProvider([]), model=" ")


def test_graph_is_provider_independent_and_serializable():
    graph = ThoughtGraphEngine(FakeProvider([HORIZONTAL])).generate_thought_graph(
        "systems", depth=1, breadth=2
    )

    payload = graph.model_dump()
    assert payload["concept"] == "systems"
    assert payload["root"]["children"][0]["name"] == "Participant eligibility"
    assert graph.model_dump_json()


def test_graph_accepts_topic_alias_without_changing_concept_api():
    graph = ThoughtGraphEngine(FakeProvider([HORIZONTAL])).generate_thought_graph(
        topic="systems", depth=1, breadth=2
    )

    assert graph.concept == "systems"
    with pytest.raises(ValueError, match="either concept or topic"):
        ThoughtGraphEngine(FakeProvider([])).generate_thought_graph(
            "systems", topic="other"
        )
