from dataclasses import dataclass

import pytest

from bot0_thought_graph.interview import (
    EvaluationService,
    InterviewContext,
    InterviewEngine,
    QuestionGenerationService,
    TopicExhaustionPolicy,
)
from bot0_thought_graph.models import EvaluationCriteria, IndexedIdeaJSONModel
from bot0_thought_graph.providers import GenerationRequest, GenerationResult, ProviderResponseError
from bot0_thought_graph.storage import MemoryRepository


@dataclass
class FakeProvider:
    responses: list[str]

    def __post_init__(self):
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.requests.append(request)
        if not self.responses:
            raise ProviderResponseError("no fake response")
        return GenerationResult(self.responses.pop(0), "fake", request.model)


GRAPH = IndexedIdeaJSONModel.model_validate(
    {
        "idea": "systems",
        "thoughts": [
            {
                "thought_index": 0,
                "thought": "hardware",
                "description": "Physical design",
                "sub_thoughts": [
                    {"sub_thought_index": 0, "name": "requirements", "description": "Define needs"},
                    {"sub_thought_index": 1, "name": "design", "description": "Choose structure"},
                ],
            },
            {
                "thought_index": 1,
                "thought": "software",
                "description": "Program logic",
                "sub_thoughts": [
                    {"sub_thought_index": 0, "name": "implementation", "description": "Build behavior"}
                ],
            },
        ],
    }
)
EVAL_HIGH = '{"evaluation":{"criteria":{"relevance":5,"correctness":5,"specificity":4,"clarity":5},"explanations":{"relevance":"Direct.","correctness":"Correct.","specificity":"Specific.","clarity":"Clear."},"total_score":4.75}}'
EVAL_LOW = '{"evaluation":{"criteria":{"relevance":3,"correctness":3,"specificity":3,"clarity":3},"explanations":{"relevance":"Partial.","correctness":"Needs work.","specificity":"General.","clarity":"Understandable."},"total_score":3.0}}'


def test_session_start_and_completion_without_persistence(tmp_path):
    provider = FakeProvider(["What are the key requirements?"])
    engine = InterviewEngine(provider, model="fake-model")
    session = engine.start(InterviewContext(idea_data=GRAPH))
    assert session.current_question == "What are the key requirements?"
    assert list(tmp_path.iterdir()) == []

    provider.responses.extend([EVAL_HIGH, "Next topic question"])
    result = engine.process_answer(session, "The requirements define system needs.")
    assert result.completed is False
    assert result.session.thought_index == 0
    assert result.session.sub_thought_index == 1
    assert result.next_question is not None


def test_follow_up_and_vertical_traversal_are_hierarchy_aware():
    provider = FakeProvider(["Initial question", EVAL_LOW, "Clarifying follow-up"])
    engine = InterviewEngine(provider, model="fake-model")
    session = engine.start(GRAPH)
    result = engine.process_answer(session, "A partial answer")
    assert result.decision == "follow_up"
    assert result.next_question == "Clarifying follow-up"
    assert result.session.thought_index == 0
    assert result.session.sub_thought_index == 0
    assert len(result.session.asked_questions) == 2


def test_completion_and_explicit_persistence():
    repository = MemoryRepository()
    provider = FakeProvider(["Initial question", EVAL_HIGH, "Next question", EVAL_HIGH, "Final question", EVAL_HIGH])
    engine = InterviewEngine(provider, model="fake-model", repository=repository)
    session = engine.start(GRAPH)
    for answer in ("one", "two", "three"):
        result = engine.process_answer(session, answer)
        session = result.session
        if result.completed:
            break
    assert session.status == "completed"
    engine.save_session(session)
    assert repository.load(session.session_id)["status"] == "completed"


def test_no_repository_save_is_explicit_and_repeated_questions_are_rejected():
    provider = FakeProvider(["Same question", EVAL_LOW, "Same question"])
    engine = InterviewEngine(provider, model="fake-model")
    session = engine.start(GRAPH)
    with pytest.raises(ProviderResponseError, match="repeated"):
        engine.process_answer(session, "partial")
    with pytest.raises(RuntimeError):
        engine.save_session(session)


def test_evaluation_and_exhaustion_boundaries():
    criteria = EvaluationCriteria(
        criteria={"relevance": 5, "correctness": 5, "specificity": 4, "clarity": 5},
        explanations={
            "relevance": "Direct.",
            "correctness": "Correct.",
            "specificity": "Specific.",
            "clarity": "Clear.",
        },
        total_score=4.75,
    )
    assert EvaluationService.meets_threshold(criteria)
    policy = TopicExhaustionPolicy({"redundancy": 0.5, "new_info": 0.3})
    policy.set_scoped_logs([{"role": "user", "message": "AI improves tasks"}])
    result = policy.evaluate("AI improves tasks")
    assert result["redundancy_score"] >= 0
    assert result["new_info_score"] >= 0


SINGLE_SUB_THOUGHT = IndexedIdeaJSONModel.model_validate(
    {
        "idea": "systems",
        "thoughts": [
            {
                "thought_index": 0,
                "thought": "hardware",
                "description": "Physical design",
                "sub_thoughts": [
                    {"sub_thought_index": 0, "name": "requirements", "description": "Define needs"}
                ],
            }
        ],
    }
)


def test_follow_up_context_logs_are_chronological():
    provider = FakeProvider(["Initial", EVAL_LOW, "Follow-1", EVAL_LOW, "Follow-2"])
    engine = InterviewEngine(provider, model="fake-model")
    session = engine.start(GRAPH)
    engine.process_answer(session, "answer one")
    result = engine.process_answer(session, "answer two")
    assert result.decision == "follow_up"
    prompt = provider.requests[-1].prompt
    assert "Agent: Initial\nUser: answer one" in prompt
    assert "Agent: Follow-1\nUser: answer two" in prompt


def test_topic_exhaustion_on_last_sub_thought_completes_session():
    provider = FakeProvider(
        [
            "Initial question",
            EVAL_LOW, "Follow-1",
            EVAL_LOW, "Follow-2",
            EVAL_LOW, "Follow-3",
            EVAL_LOW, "Follow-4",
        ]
    )
    engine = InterviewEngine(provider, model="fake-model")
    session = engine.start(SINGLE_SUB_THOUGHT)
    result = None
    for _ in range(6):
        result = engine.process_answer(session, "the same answer repeated over and over again")
        session = result.session
        if result.completed:
            break
    assert result is not None and result.completed
    assert session.status == "completed"
    assert result.topic_exhausted is True
    assert result.decision_reason == "Topic exhaustion threshold reached; no remaining topics."


def test_exhaustion_policy_reset_between_sessions():
    policy = TopicExhaustionPolicy({"redundancy": 0.5, "new_info": 0.3})
    provider = FakeProvider(["Q1", EVAL_HIGH])
    engine = InterviewEngine(provider, model="fake-model", exhaustion_policy=policy)
    first = engine.start(SINGLE_SUB_THOUGHT)
    first_result = engine.process_answer(first, "alpha beta")
    assert first_result.completed
    provider.responses.extend(["Q2", EVAL_HIGH])
    second = engine.start(SINGLE_SUB_THOUGHT)
    second_result = engine.process_answer(second, "alpha beta")
    assert second.exhaustion_state["is_exhausted"] is False
    assert second_result.completed


from bot0_thought_graph.interview.state import has_current_sub_thought, next_location
from bot0_thought_graph.orchestration.coordinator import InterviewCoordinator
from bot0_thought_graph.orchestration.policies import InterviewPolicy


def test_state_traversal_helpers():
    assert has_current_sub_thought(GRAPH, 0, 0) is True
    assert has_current_sub_thought(GRAPH, 0, 1) is True
    assert has_current_sub_thought(GRAPH, 0, 2) is False
    assert has_current_sub_thought(GRAPH, 2, 0) is False
    assert next_location(GRAPH, 0, 0) == (0, 1)
    assert next_location(GRAPH, 0, 1) == (1, 0)
    assert next_location(GRAPH, 1, 0) is None


def test_interview_policy_defaults_and_override():
    assert InterviewPolicy().correctness_threshold == 4.5
    assert InterviewPolicy().max_follow_up_questions is None
    assert InterviewPolicy(correctness_threshold=3.0).correctness_threshold == 3.0
    assert InterviewPolicy(max_follow_up_questions=2).max_follow_up_questions == 2


def test_coordinator_delegates_start_process_and_save():
    repository = MemoryRepository()
    provider = FakeProvider(["Initial question", EVAL_HIGH, "Next question", EVAL_HIGH, "Final question", EVAL_HIGH])
    coordinator = InterviewCoordinator(
        InterviewEngine(provider, model="fake-model", repository=repository)
    )
    session = coordinator.start(GRAPH)
    assert session.current_question == "Initial question"
    result = coordinator.process_answer(session, "one")
    assert result.completed is False
    coordinator.save_session(result.session)
    assert repository.load(result.session.session_id)["status"] == "active"
