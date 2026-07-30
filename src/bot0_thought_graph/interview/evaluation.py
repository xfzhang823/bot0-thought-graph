"""Provider-injected answer evaluation."""

from bot0_thought_graph.models import EvaluationCriteria, EvaluationJSONModel
from bot0_thought_graph.prompts import QUESTION_ANSWER_EVAL_PROMPT
from bot0_thought_graph.providers import GenerationRequest, LLMProvider, ProviderResponseError
from bot0_thought_graph.thought_generation.parsing import extract_json


class EvaluationService:
    """Evaluate answers into the package's existing evaluation schema."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1056,
        timeout: float | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def evaluate(self, *, question: str, answer: str, idea: str, thought: str) -> EvaluationCriteria:
        prompt = QUESTION_ANSWER_EVAL_PROMPT.format(
            question=question, answer=answer, idea=idea, thought=thought
        )
        result = self.provider.generate(
            GenerationRequest(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
        )
        try:
            return EvaluationJSONModel(**extract_json(result.text)).evaluation
        except Exception as exc:
            raise ProviderResponseError("Provider returned an invalid evaluation") from exc

    @staticmethod
    def composite_score(criteria: EvaluationCriteria) -> float:
        return round(sum(criteria.criteria.values()) / len(criteria.criteria), 2) if criteria.criteria else 0.0

    @staticmethod
    def meets_threshold(criteria: EvaluationCriteria, threshold: float = 4.5) -> bool:
        return criteria.criteria.get("correctness", 0) >= threshold
