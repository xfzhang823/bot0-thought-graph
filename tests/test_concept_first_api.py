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
VERTICAL_ONE_CHILD = (
    '{"idea":"Clinical research recruitment","thought":"next",'
    '"sub_thoughts":[{"name":"next level","description":"Further detail"}]}'
)


def horizontal_response(name):
    return (
        '{"idea":"Clinical research recruitment","thoughts":['
        f'{{"thought":"{name}","description":"A direction"}}]}}'
    )


def vertical_response(*names):
    children = ",".join(
        f'{{"name":"{name}","description":"Further detail"}}'
        for name in names
    )
    return (
        '{"idea":"Clinical research recruitment","thought":"parent",'
        f'"sub_thoughts":[{children}]}}'
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


def test_graph_supports_independent_horizontal_and_vertical_bounds():
    provider = FakeProvider([HORIZONTAL] + [VERTICAL_ONE_CHILD] * 14)
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=8,
    )

    assert graph.breadth == 2
    assert graph.depth == 8
    assert len(graph.root.children) == 2
    assert len(provider.requests) == 15  # one horizontal call plus 7 per branch
    assert all("exactly 7" in request.prompt for request in provider.requests[1:])
    assert all("exactly 2" not in request.prompt for request in provider.requests[1:])

    def leaf_depth(node):
        if not node.children:
            return 1
        return 1 + max(leaf_depth(child) for child in node.children)

    assert [leaf_depth(child) for child in graph.root.children] == [8, 8]


def test_horizontal_bound_is_not_reused_for_vertical_children():
    provider = FakeProvider([HORIZONTAL, VERTICAL, VERTICAL])
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=2,
    )

    assert len(graph.root.children) == 2
    assert [len(child.children) for child in graph.root.children] == [3, 3]
    assert all("exactly 7" in request.prompt for request in provider.requests[1:])


def test_explicit_dimensions_do_not_cross_influence_request_sizes():
    narrow_provider = FakeProvider([HORIZONTAL, VERTICAL])
    narrow_graph = ThoughtGraphEngine(narrow_provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=1,
        vertical=2,
    )

    wide_provider = FakeProvider([HORIZONTAL, VERTICAL, VERTICAL, VERTICAL])
    wide_graph = ThoughtGraphEngine(wide_provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=3,
        vertical=2,
    )

    assert len(narrow_graph.root.children) == 1
    assert len(wide_graph.root.children) == 3
    assert "exactly 1" in narrow_provider.requests[0].prompt
    assert "exactly 3" in wide_provider.requests[0].prompt
    assert all(
        "exactly 7" in request.prompt for request in narrow_provider.requests[1:]
    )
    assert all(
        "exactly 7" in request.prompt for request in wide_provider.requests[1:]
    )

    shallow_provider = FakeProvider([HORIZONTAL])
    deep_provider = FakeProvider([HORIZONTAL] + [VERTICAL_ONE_CHILD] * 14)
    ThoughtGraphEngine(shallow_provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=1,
    )
    ThoughtGraphEngine(deep_provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=8,
    )
    assert shallow_provider.requests[0].prompt == deep_provider.requests[0].prompt


@pytest.mark.parametrize("vertical", [1, 2, 3])
def test_new_vertical_bound_has_no_off_by_one(vertical):
    provider = FakeProvider([HORIZONTAL] + [VERTICAL_ONE_CHILD] * (2 * vertical))
    graph = ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=vertical,
    )

    assert len(provider.requests) == 1 + 2 * (vertical - 1)

    def leaf_depth(node):
        if not node.children:
            return 1
        return 1 + max(leaf_depth(child) for child in node.children)

    assert [leaf_depth(child) for child in graph.root.children] == [vertical, vertical]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"depth": 2, "horizontal": 2},
        {"breadth": 3, "vertical": 4},
        {"depth": 2, "vertical": 4},
        {"breadth": 3, "horizontal": 2},
    ],
)
def test_new_bounds_reject_mixed_legacy_bounds_before_provider_calls(kwargs):
    provider = FakeProvider([])
    with pytest.raises(ValueError, match="cannot be combined"):
        ThoughtGraphEngine(provider).generate_thought_graph("systems", **kwargs)
    assert provider.requests == []


@pytest.mark.parametrize(
    ("keyword", "value"),
    [
        ("horizontal", 0),
        ("horizontal", -1),
        ("horizontal", True),
        ("horizontal", 1.5),
        ("horizontal", "2"),
        ("vertical", 0),
        ("vertical", -1),
        ("vertical", False),
        ("vertical", 1.5),
        ("vertical", "2"),
        ("vertical", 9),
    ],
)
def test_new_bounds_reject_invalid_values_before_provider_calls(keyword, value):
    provider = FakeProvider([])
    with pytest.raises(ValueError, match=keyword):
        ThoughtGraphEngine(provider).generate_thought_graph(
            "systems", **{keyword: value}
        )
    assert provider.requests == []


def test_legacy_depth_retains_the_previous_maximum():
    provider = FakeProvider([])
    with pytest.raises(ValueError, match="depth must be <= 3"):
        ThoughtGraphEngine(provider).generate_thought_graph("systems", depth=4)
    assert provider.requests == []


def test_progression_type_remains_vertical_only_with_new_bounds():
    provider = FakeProvider([HORIZONTAL, VERTICAL, VERTICAL])
    ThoughtGraphEngine(provider).generate_thought_graph(
        "Clinical research recruitment",
        horizontal=2,
        vertical=2,
        progression_type="prerequisite_dependency",
    )

    assert "Progression type:" not in provider.requests[0].prompt
    assert all(
        'Progression type: "prerequisite_dependency"' in request.prompt
        for request in provider.requests[1:]
    )


def adaptive_responses(horizontal_names, vertical_responses):
    return (
        [horizontal_response(name) for name in horizontal_names]
        + list(vertical_responses)
    )


def test_default_adaptive_mode_is_balanced_and_records_stop_reasons():
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Architecture"],
            [vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph("Clinical research recruitment")

    assert engine.last_exploration_profile == "balanced"
    assert graph.breadth == 1
    assert graph.depth == 1
    assert any(
        decision.reason == "insufficient_distinctness"
        for decision in engine.last_exploration_trace
    )
    assert any(
        decision.reason == "no_children"
        for decision in engine.last_exploration_trace
    )
    assert all(
        decision.reason.value
        in {
            "depth_limit",
            "insufficient_distinctness",
            "insufficient_novelty",
            "internal_candidate_limit",
            "materially_distinct",
            "meaningful_children",
            "natural_endpoint",
            "no_candidate",
            "no_children",
        }
        for decision in engine.last_exploration_trace
    )


def test_adaptive_profiles_are_monotonic_for_horizontal_continuation():
    counts = []
    for profile, horizontal_names in [
        ("focused", ["Architecture", "Architecture design"]),
        (
            "balanced",
            ["Architecture", "Architecture design", "Architecture design strategy"],
        ),
        (
            "rich",
            [
                "Architecture",
                "Architecture design",
                "Architecture design strategy",
                "Architecture design strategy",
            ],
        ),
    ]:
        provider = FakeProvider(
            [horizontal_response(name) for name in horizontal_names]
            + [vertical_response()] * 3
        )
        engine = ThoughtGraphEngine(provider)
        graph = engine.generate_thought_graph(
            "Clinical research recruitment", exploration=profile
        )
        counts.append(len(graph.root.children))
        assert any(
            decision.axis == "horizontal" and decision.action == "stop"
            for decision in engine.last_exploration_trace
        )

    assert counts[0] <= counts[1] <= counts[2]


def test_adaptive_profiles_are_monotonic_for_vertical_continuation():
    depths = []
    for profile in ("focused", "balanced", "rich"):
        provider = FakeProvider(
            [
                horizontal_response("Architecture"),
                horizontal_response("Architecture"),
                vertical_response("Architecture design"),
                vertical_response("Architecture design strategy"),
                vertical_response(),
            ]
        )
        engine = ThoughtGraphEngine(provider)
        graph = engine.generate_thought_graph(
            "Clinical research recruitment", exploration=profile
        )
        depths.append(graph.depth)
        assert any(
            decision.axis == "vertical"
            and (
                decision.action == "stop"
                or decision.reason in {"branch_pruned", "natural_endpoint"}
            )
            for decision in engine.last_exploration_trace
        )

    assert depths[0] <= depths[1] <= depths[2]


def test_adaptive_retains_pruned_children_but_only_expands_useful_branches():
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Architecture"],
            [vertical_response("Architecture design", "Operations"), vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert [child.name for child in graph.root.children] == ["Architecture"]
    assert [child.name for child in graph.root.children[0].children] == [
        "Architecture design",
        "Operations",
    ]
    assert len(provider.requests) == 4
    assert any(
        decision.reason == "branch_pruned"
        and decision.action == "retain"
        and decision.thought == "Architecture design"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_vertical_selection_deduplicates_sibling_children():
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Architecture"],
            [
                vertical_response("Design", "Design", "Operations"),
                vertical_response(),
                vertical_response(),
            ],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="rich"
    )

    assert [child.name for child in graph.root.children[0].children] == [
        "Design",
        "Operations",
    ]


def test_adaptive_branch_continuation_is_monotonic_across_profiles():
    calls = []
    for profile in ("focused", "balanced", "rich"):
        provider = FakeProvider(
            adaptive_responses(
                ["Architecture", "Architecture"],
                [
                    vertical_response("Architecture design", "Operations"),
                    vertical_response(),
                    vertical_response(),
                ],
            )
        )
        engine = ThoughtGraphEngine(provider)
        engine.generate_thought_graph(
            "Clinical research recruitment", exploration=profile
        )
        calls.append(len(provider.requests))

    assert calls[0] <= calls[1] <= calls[2]


def test_adaptive_call_budget_returns_partial_graph_with_safety_trace(monkeypatch):
    monkeypatch.setattr(ThoughtGraphEngine, "_ADAPTIVE_MAX_PROVIDER_CALLS", 1)
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Operations"],
            [],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert [child.name for child in graph.root.children] == ["Architecture"]
    assert any(decision.reason == "call_budget" for decision in engine.last_exploration_trace)


def test_adaptive_node_budget_preserves_completed_nodes(monkeypatch):
    monkeypatch.setattr(ThoughtGraphEngine, "_ADAPTIVE_MAX_NODES", 2)
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Operations"],
            [],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert [child.name for child in graph.root.children] == ["Architecture"]
    assert any(decision.reason == "node_budget" for decision in engine.last_exploration_trace)


def test_adaptive_expansion_budget_stops_before_next_provider_call(monkeypatch):
    monkeypatch.setattr(ThoughtGraphEngine, "_ADAPTIVE_MAX_EXPANSIONS", 1)
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Architecture"],
            [],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert [child.name for child in graph.root.children] == ["Architecture"]
    assert len(provider.requests) == 1
    assert any(
        decision.reason == "expansion_budget"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_semantic_stop_is_distinct_from_safety_stop():
    provider = FakeProvider(
        adaptive_responses(["Architecture", "Architecture"], [vertical_response()])
    )
    engine = ThoughtGraphEngine(provider)
    engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    reasons = {decision.reason.value for decision in engine.last_exploration_trace}
    assert "no_children" in reasons
    assert not reasons & {"call_budget", "node_budget", "expansion_budget"}


def test_adaptive_horizontal_rejects_duplicates_and_keeps_distinct_directions():
    provider = FakeProvider(
        adaptive_responses(
            ["Architecture", "Operations", "Architecture"],
            [vertical_response(), vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment",
        exploration="balanced",
    )

    assert [child.name for child in graph.root.children] == ["Architecture", "Operations"]
    assert any(
        decision.reason == "insufficient_distinctness"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_novelty_normalizes_trivial_rephrasing_and_stop_words():
    provider = FakeProvider(
        adaptive_responses(
            ["System design", "Design of the system"],
            [vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="rich"
    )

    assert [child.name for child in graph.root.children] == ["System design"]
    assert any(
        decision.reason == "insufficient_distinctness"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_novelty_keeps_related_but_distinct_directions():
    provider = FakeProvider(
        adaptive_responses(
            ["Data collection", "Data analysis", "Data collection"],
            [vertical_response(), vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert [child.name for child in graph.root.children] == [
        "Data collection",
        "Data analysis",
    ]


def test_adaptive_low_lexical_overlap_is_not_claimed_as_semantic_duplicate():
    provider = FakeProvider(
        adaptive_responses(
            ["Vehicle safety", "Automobile safety", "Vehicle safety"],
            [vertical_response(), vertical_response()],
        )
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="rich"
    )

    assert [child.name for child in graph.root.children] == [
        "Vehicle safety",
        "Automobile safety",
    ]


def test_adaptive_repeated_vertical_descendant_stops_the_branch():
    provider = FakeProvider(
        [
            horizontal_response("Architecture"),
            horizontal_response("Architecture"),
            vertical_response("Architecture design"),
            vertical_response("Architecture design"),
        ]
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="rich"
    )

    assert graph.depth == 2
    assert any(
        decision.reason == "insufficient_novelty"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_vertical_stops_at_natural_endpoint():
    provider = FakeProvider(
        [
            horizontal_response("Architecture"),
            horizontal_response("Architecture"),
            vertical_response("Final summary"),
        ]
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment",
        exploration="balanced",
        progression_type="prerequisite_dependency",
    )

    assert graph.depth == 2
    assert "Progression type:" not in provider.requests[0].prompt
    assert 'Progression type: "prerequisite_dependency"' in provider.requests[2].prompt
    assert any(
        decision.reason == "natural_endpoint"
        for decision in engine.last_exploration_trace
    )
    assert len(provider.requests) == 3


def test_endpoint_terms_are_supporting_signals_not_keyword_only_stops():
    provider = FakeProvider(
        [
            horizontal_response("Architecture"),
            horizontal_response("Architecture"),
            vertical_response("Summary metrics"),
            vertical_response(),
        ]
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="balanced"
    )

    assert graph.depth == 2
    assert len(provider.requests) == 4
    assert any(
        decision.reason == "no_children"
        for decision in engine.last_exploration_trace
    )
    assert not any(
        decision.reason == "natural_endpoint"
        and decision.thought == "Summary metrics"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_branches_can_stop_at_different_depths():
    provider = FakeProvider(
        [
            horizontal_response("Architecture"),
            horizontal_response("Operations"),
            horizontal_response("Architecture"),
            vertical_response(),
            vertical_response("Operations execution"),
            vertical_response(),
        ]
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment",
        exploration="balanced",
    )

    assert [
        1 if not child.children else 2 for child in graph.root.children
    ] == [1, 2]
    assert graph.depth == 2


def test_adaptive_horizontal_guard_is_internal_and_profile_independent():
    horizontal_names = [
        "Architecture",
        "Operations",
        "Measurement",
        "Recruitment",
        "Compliance",
        "Technology",
        "Governance",
        "Outcomes",
    ]
    provider = FakeProvider(
        [horizontal_response(name) for name in horizontal_names]
        + [vertical_response()] * 8
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="focused"
    )

    assert len(graph.root.children) == 8
    assert any(
        decision.reason == "internal_candidate_limit"
        for decision in engine.last_exploration_trace
    )


def test_adaptive_vertical_guard_stops_at_the_internal_depth_limit():
    provider = FakeProvider(
        [horizontal_response("Architecture"), horizontal_response("Architecture")]
        + [vertical_response(f"Level {index}") for index in range(1, 8)]
    )
    engine = ThoughtGraphEngine(provider)
    graph = engine.generate_thought_graph(
        "Clinical research recruitment", exploration="rich"
    )

    assert graph.depth == engine.MAX_FACADE_DEPTH
    assert any(
        decision.reason == "depth_limit"
        for decision in engine.last_exploration_trace
    )


@pytest.mark.parametrize("value", ["unknown", "", 1, True])
def test_invalid_exploration_is_rejected_before_provider_calls(value):
    provider = FakeProvider([])
    with pytest.raises(ValueError, match="exploration"):
        ThoughtGraphEngine(provider).generate_thought_graph(
            "systems", exploration=value
        )
    assert provider.requests == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"exploration": "balanced", "horizontal": 2},
        {"exploration": "balanced", "vertical": 8},
        {"exploration": "balanced", "depth": 2},
        {"exploration": "balanced", "breadth": 3},
    ],
)
def test_adaptive_mode_rejects_shape_bounds_before_provider_calls(kwargs):
    provider = FakeProvider([])
    with pytest.raises(ValueError, match="exploration cannot be combined"):
        ThoughtGraphEngine(provider).generate_thought_graph("systems", **kwargs)
    assert provider.requests == []


@pytest.mark.parametrize(
    "call",
    [
        lambda engine: engine.generate_subtopics(" "),
        lambda engine: engine.expand_subtopic("concept", "\t"),
        lambda engine: engine.generate_subtopics("concept", max_subtopics=0),
        lambda engine: engine.expand_subtopic("concept", "topic", max_details=-1),
        lambda engine: engine.generate_thought_graph("concept", depth=0),
        lambda engine: engine.generate_thought_graph("concept", breadth=0),
        lambda engine: engine.generate_thought_graph("concept", depth=9),
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
