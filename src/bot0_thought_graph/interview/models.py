"""Typed in-memory interview models."""

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from bot0_thought_graph.models import EvaluationCriteria, IndexedIdeaJSONModel


class InterviewContext(BaseModel):
    """The indexed thought graph that bounds an interview."""

    idea_data: IndexedIdeaJSONModel


class SessionMetadata(BaseModel):
    total_interactions: int = 0
    average_response_time: float | None = None


class InterviewTurn(BaseModel):
    question: str
    answer: str
    evaluation: EvaluationCriteria | None = None
    thought_index: int
    sub_thought_index: int


class InterviewSession(BaseModel):
    """Complete interview state; no filesystem or provider objects are stored."""

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    context: InterviewContext
    thought_index: int = 0
    sub_thought_index: int = 0
    current_question: str | None = None
    asked_questions: list[str] = Field(default_factory=list)
    turns: list[InterviewTurn] = Field(default_factory=list)
    current_evaluation: EvaluationCriteria | None = None
    evaluations: list[EvaluationCriteria] = Field(default_factory=list)
    session_metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    status: Literal["active", "completed"] = "active"
    exhaustion_state: dict[str, float | bool] | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class InterviewTurnResult(BaseModel):
    """Typed result returned after processing one answer."""

    session: InterviewSession
    evaluation: EvaluationCriteria
    next_question: str | None = None
    topic_exhausted: bool = False
    completed: bool = False
    decision: str
    decision_reason: str


class ReflectionDecision(BaseModel):
    action: Literal["advance", "follow_up", "complete"]
    reason: str
    should_clarify: bool = False
