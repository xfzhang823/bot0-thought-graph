"""Legacy compatibility exports for topic-exhaustion policy."""

from bot0_thought_graph.interview.topic_exhaustion import (
    ConversationMetrics,
    TopicExhaustionPolicy,
)

TopicExhaustionService = TopicExhaustionPolicy

__all__ = ["ConversationMetrics", "TopicExhaustionPolicy", "TopicExhaustionService"]
