"""Provider-backed vertical thought expansion."""

from bot0_thought_graph.models import IdeaJSONModel, ThoughtJSONModel
from bot0_thought_graph.prompts import VERTICAL_SUB_THOUGHT_GENERATION_PROMPT
from bot0_thought_graph.providers import GenerationRequest, LLMProvider

from .validation import parse_thought


def expand_vertical(
    provider: LLMProvider,
    *,
    idea: str,
    thought: str,
    model: str,
    progression_type: str = "implementation_steps",
    num_sub_thoughts: int = 7,
    temperature: float = 0.7,
    max_tokens: int = 1056,
    timeout: float | None = None,
    prompt_template: str | None = None,
) -> ThoughtJSONModel:
    """Generate and validate sub-thoughts for one high-level thought."""
    prompt_template = prompt_template or VERTICAL_SUB_THOUGHT_GENERATION_PROMPT
    prompt = prompt_template.format(
        thought=thought,
        num_sub_thoughts=num_sub_thoughts,
        progression_type=progression_type,
        idea=idea,
    )
    result = provider.generate(
        GenerationRequest(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    )
    return parse_thought(result.text)


def expand_idea(
    provider: LLMProvider,
    idea_model: IdeaJSONModel,
    *,
    model: str,
    progression_type: str = "implementation_steps",
    num_sub_thoughts: int = 5,
    temperature: float = 0.7,
    max_tokens: int = 1056,
    timeout: float | None = None,
) -> IdeaJSONModel:
    """Expand each existing thought in input order and return an in-memory idea."""
    expanded = []
    for thought in idea_model.thoughts or []:
        generated = expand_vertical(
            provider,
            idea=idea_model.idea,
            thought=thought.thought,
            model=model,
            progression_type=progression_type,
            num_sub_thoughts=num_sub_thoughts,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        generated.description = thought.description
        expanded.append(generated)
    return IdeaJSONModel(idea=idea_model.idea, thoughts=expanded)
