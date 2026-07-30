"""Replaceable orchestration policies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewPolicy:
    correctness_threshold: float = 4.5
    max_follow_up_questions: int | None = None
