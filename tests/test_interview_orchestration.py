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
