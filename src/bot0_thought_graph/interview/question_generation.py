"""Provider-injected interview question generation."""

from collections.abc import Sequence

from bot0_thought_graph.models import EvaluationCriteria
from bot0_thought_graph.prompts import (
    FOLLOWUP_QUESTION_GENERATION_PROMPT,
    INITIAL_QUESTION_GENERATION_PROMPT,
)
from bot0_thought_graph.providers import GenerationRequest, LLMProvider, ProviderResponseError


class QuestionGenerationService:
    """Generate unique questions without owning session lifecycle."""

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

    @staticmethod
    def complexity(complexity: str) -> str:
        return {
            "simple": "straightforward and easy to understand",
            "moderate": "thought-provoking and requiring some reflection",
            "advanced": "complex and requiring deep analytical thinking",
        }.get(complexity, "thought-provoking and requiring some reflection")

    def _generate(self, prompt: str, asked_questions: Sequence[str]) -> str:
        result = self.provider.generate(
            GenerationRequest(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout,
            )
        )
        question = result.text.strip()
        if not question:
            raise ProviderResponseError("Provider returned an empty interview question")
        if question in asked_questions:
            raise ProviderResponseError("Provider repeated an interview question")
        return question

    def initial(
        self,
        *,
        topic_name: str,
        context_text: str | None = None,
        complexity: str = "moderate",
        asked_questions: Sequence[str] = (),
    ) -> str:
        context = f"Context:\n{context_text}" if context_text else "No additional context provided."
        prompt = INITIAL_QUESTION_GENERATION_PROMPT.format(
            complexity_level=self.complexity(complexity),
            topic_name=topic_name,
            context=context,
        )
        return self._generate(prompt, asked_questions)

    def follow_up(
        self,
        *,
        evaluation: EvaluationCriteria,
        idea: str,
        thought: str,
        sub_thought_description: str,
        context_logs: Sequence[dict[str, str]],
        asked_questions: Sequence[str] = (),
    ) -> str:
        scores = "\n".join(
            f"- {criterion.capitalize()}: {score}/5, {evaluation.explanations[criterion]}"
            for criterion, score in evaluation.criteria.items()
        )
        conversation = "\n".join(
            f"{entry['role'].capitalize()}: {entry['message']}" for entry in context_logs
        )
        prompt = FOLLOWUP_QUESTION_GENERATION_PROMPT.format(
            idea=idea,
            main_thought=thought,
            sub_thought_description=sub_thought_description,
            evaluation_scores_and_explanations=scores,
            conversation_context=conversation,
        )
        return self._generate(prompt, asked_questions)
