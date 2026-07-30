"""Provider-backed horizontal thought generation."""

from bot0_thought_graph.models import IdeaJSONModel
from bot0_thought_graph.prompts import THOUGHT_GENERATION_PROMPT
from bot0_thought_graph.providers import GenerationRequest, LLMProvider

from .validation import parse_idea


def generate_horizontal(
    provider: LLMProvider,
    *,
    idea: str,
    model: str,
    num_thoughts: int = 10,
    temperature: float = 0.7,
    max_tokens: int = 1056,
    timeout: float | None = None,
    prompt_template: str = THOUGHT_GENERATION_PROMPT,
) -> IdeaJSONModel:
    """Generate and validate high-level thoughts using an injected provider."""
    prompt = prompt_template.format(idea=idea, num_sub_thoughts=num_thoughts)
    result = provider.generate(
        GenerationRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    )
    return parse_idea(result.text)
