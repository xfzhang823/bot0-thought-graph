"""Deterministic models for evaluating interview answers."""

import logging
from typing import Dict

from pydantic import BaseModel, Field, ValidationInfo, field_validator

logger = logging.getLogger(__name__)
CRITERIA_KEYS = {"relevance", "correctness", "specificity", "clarity"}


class EvaluationCriteria(BaseModel):
    criteria: Dict[str, int] = Field(..., min_length=4, max_length=4)
    explanations: Dict[str, str] = Field(..., min_length=4, max_length=4)
    total_score: float

    @field_validator("criteria")
    def validate_criteria(cls, v):
        if not isinstance(v, dict):
            raise TypeError(f"Expected a dictionary for criteria, but got {type(v)}.")
        if set(v.keys()) != CRITERIA_KEYS:
            missing = CRITERIA_KEYS - set(v.keys())
            extra = set(v.keys()) - CRITERIA_KEYS
            error_msg = ""
            if missing:
                error_msg += f"Missing criteria keys: {missing}. "
            if extra:
                error_msg += f"Unexpected criteria keys: {extra}."
            raise ValueError(error_msg.strip())
        for key, score in v.items():
            if not isinstance(score, int):
                raise TypeError(f"Score for '{key}' must be an integer.")
            if not 1 <= score <= 5:
                raise ValueError(f"Score for '{key}' must be between 1 and 5. Got {score}.")
        return v

    @field_validator("explanations")
    def validate_explanations(cls, v):
        if not isinstance(v, dict):
            raise TypeError(f"Expected a dictionary for explanations, but got {type(v)}.")
        if set(v.keys()) != CRITERIA_KEYS:
            missing = CRITERIA_KEYS - set(v.keys())
            extra = set(v.keys()) - CRITERIA_KEYS
            error_msg = ""
            if missing:
                error_msg += f"Missing explanation keys: {missing}. "
            if extra:
                error_msg += f"Unexpected explanation keys: {extra}."
            raise ValueError(error_msg.strip())
        for key, explanation in v.items():
            if not isinstance(explanation, str):
                raise TypeError(f"Explanation for '{key}' must be a string.")
            word_count = len(explanation.split())
            if word_count > 50:
                raise ValueError(
                    f"Explanation for '{key}' exceeds 50 words (currently {word_count} words)."
                )
        return v


class QuestionAnswerPair(BaseModel):
    question: str
    answer: str

    @field_validator("question", "answer")
    def validate_non_empty(cls, v, info: ValidationInfo):
        field_name = info.field_name
        if not v:
            raise ValueError(f"{field_name} cannot be empty")
        return v


class EvaluationJSONModel(BaseModel):
    evaluation: EvaluationCriteria

    @field_validator("evaluation")
    def validate_evaluation(cls, v):
        return v
