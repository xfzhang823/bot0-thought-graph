"""Deterministic topic-exhaustion policy."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ConversationMetrics:
    redundancy_score: float = 0.0
    new_info_score: float = 0.0
    exchange_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)

    def is_exhausted(self, threshold: dict[str, float]) -> bool:
        return (
            self.redundancy_score > threshold["redundancy"]
            and self.new_info_score < threshold["new_info"]
        )


class TopicExhaustionPolicy:
    """Preserve legacy overlap/new-information thresholds without persistence."""

    def __init__(self, thresholds: dict[str, float] | None = None) -> None:
        self.thresholds = thresholds or {"redundancy": 0.7, "new_info": 0.2}
        self.reset()

    def reset(self) -> None:
        self.keywords: set[str] = set()
        self.previous_responses: list[str] = []
        self.metrics = ConversationMetrics()
        self.scoped_logs: list[dict[str, str]] = []

    def set_scoped_logs(self, scoped_logs: list[dict[str, str]]) -> None:
        if not isinstance(scoped_logs, list) or not all(isinstance(item, dict) for item in scoped_logs):
            raise ValueError("Scoped logs must be a list of dictionaries.")
        self.scoped_logs = scoped_logs
        self.previous_responses = [item["message"] for item in scoped_logs if item.get("role") == "user"]

    def _calculate_redundancy(self, answer: str) -> float:
        if not self.previous_responses:
            self.previous_responses.append(answer)
            return 0.0
        current_words = set(answer.lower().split())
        total_overlap = 0.0
        for previous in self.previous_responses:
            previous_words = set(previous.lower().split())
            total_overlap += len(current_words.intersection(previous_words)) / len(current_words) if current_words else 0
        self.previous_responses.append(answer)
        return total_overlap / len(self.previous_responses)

    def _calculate_new_info(self, answer: str) -> float:
        words = set(answer.lower().split())
        new_words = words - self.keywords
        self.keywords.update(words)
        return len(new_words) / len(words) if words else 0.0

    def evaluate(self, answer: str) -> dict[str, bool | float]:
        self.metrics.exchange_count += 1
        self.metrics.last_update = datetime.now()
        self.metrics.redundancy_score = self._calculate_redundancy(answer)
        self.metrics.new_info_score = self._calculate_new_info(answer)
        exhausted = self.metrics.is_exhausted(self.thresholds)
        return {
            "is_exhausted": exhausted,
            "redundancy_score": self.metrics.redundancy_score,
            "new_info_score": self.metrics.new_info_score,
        }

    is_topic_exhausted = evaluate
