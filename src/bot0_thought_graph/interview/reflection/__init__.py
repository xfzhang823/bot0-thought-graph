"""Reflection capabilities used by the interview subsystem.

Reflection is the broader metacognitive boundary.  Its capabilities retain
separate contracts: answer evaluation assesses answer quality, while future
decomposition evaluation will assess whether a thought merits another graph
level.
"""

from .answer_evaluation import EvaluationService
from .policy import ReflectionService

__all__ = ["EvaluationService", "ReflectionService"]
