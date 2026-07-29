import pytest
from pydantic import ValidationError

from bot0_thought_graph.models import (
    EvaluationCriteria,
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    IndexedSubThoughtJSONModel,
    IndexedThoughtJSONModel,
    QuestionAnswerPair,
    TextResponse,
)
from bot0_thought_graph.prompts import (
    FOLLOWUP_QUESTION_GENERATION_PROMPT,
    QUESTION_ANSWER_EVAL_PROMPT,
    THOUGHT_GENERATION_PROMPT,
)
from models.evaluation_models import EvaluationCriteria as LegacyEvaluationCriteria
from models.thought_models import IdeaJSONModel as LegacyIdeaJSONModel
from prompts.thought_generation_prompt_templates import (
    THOUGHT_GENERATION_PROMPT as LegacyThoughtGenerationPrompt,
)


def test_package_models_are_public_and_legacy_models_are_compatible():
    assert LegacyIdeaJSONModel is IdeaJSONModel
    assert LegacyEvaluationCriteria is EvaluationCriteria
    assert TextResponse(content="hello").model_dump() == {"content": "hello"}


def test_thought_model_defaults_and_serialization():
    model = IdeaJSONModel(idea="climate")
    assert model.thoughts is None
    assert model.model_dump() == {"idea": "climate", "thoughts": None}


def test_indexed_thought_hierarchy_is_validated():
    model = IndexedIdeaJSONModel(
        idea="systems",
        thoughts=[
            IndexedThoughtJSONModel(
                thought_index=0,
                thought="requirements",
                sub_thoughts=[
                    IndexedSubThoughtJSONModel(
                        sub_thought_index=0,
                        name="scope",
                        description="Define scope.",
                    )
                ],
            )
        ],
    )
    assert model.thoughts[0].sub_thoughts[0].sub_thought_index == 0


def test_evaluation_validation_and_question_answer_defaults():
    valid = {
        "criteria": {
            "relevance": 4,
            "correctness": 4,
            "specificity": 3,
            "clarity": 5,
        },
        "explanations": {
            "relevance": "Relevant.",
            "correctness": "Correct.",
            "specificity": "Specific.",
            "clarity": "Clear.",
        },
        "total_score": 4.0,
    }
    assert EvaluationCriteria(**valid).total_score == 4.0
    with pytest.raises(ValidationError):
        EvaluationCriteria(**{**valid, "criteria": {"relevance": 6}})
    with pytest.raises(ValidationError):
        QuestionAnswerPair(question="", answer="answer")


def test_prompt_exports_and_rendering():
    assert LegacyThoughtGenerationPrompt is THOUGHT_GENERATION_PROMPT
    rendered = THOUGHT_GENERATION_PROMPT.format(idea="AI", num_sub_thoughts=3)
    assert '"idea": "AI"' in rendered
    assert "{num_sub_thoughts}" not in rendered
    assert "{question}" in QUESTION_ANSWER_EVAL_PROMPT
    assert "{conversation_context}" in FOLLOWUP_QUESTION_GENERATION_PROMPT
