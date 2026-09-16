"""Compatibility import for the answer-evaluation capability.

New code should import it from :mod:`bot0_thought_graph.interview.reflection`.
"""

from .reflection.answer_evaluation import EvaluationService

__all__ = ["EvaluationService"]
