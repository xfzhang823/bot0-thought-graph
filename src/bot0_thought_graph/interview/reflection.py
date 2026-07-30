"""Deterministic reflection and next-action decisions."""

from bot0_thought_graph.models import EvaluationCriteria

from .models import ReflectionDecision


class ReflectionService:
    """Separate policy decisions from provider-generated evaluation."""

    def __init__(self, correctness_threshold: float = 4.5) -> None:
        self.correctness_threshold = correctness_threshold

    def decide(self, evaluation: EvaluationCriteria, *, has_next_topic: bool) -> ReflectionDecision:
        if evaluation.criteria.get("correctness", 0) >= self.correctness_threshold:
            return ReflectionDecision(
                action="advance" if has_next_topic else "complete",
                reason="The answer met the correctness threshold.",
                should_clarify=False,
            )
        return ReflectionDecision(
            action="follow_up",
            reason="The answer did not meet the correctness threshold.",
            should_clarify=True,
        )
