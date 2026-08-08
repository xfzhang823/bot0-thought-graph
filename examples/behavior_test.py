"""Live smoke test for the concept-first thought-generation façade."""

from __future__ import annotations

import os
import time

from bot0_thought_graph import ThoughtGraphEngine
from bot0_thought_graph.providers.contracts import LLMProvider
from bot0_thought_graph.providers.deepseek import DeepSeekProvider
from bot0_thought_graph.providers.gemini import GeminiProvider
from bot0_thought_graph.providers.openai import OpenAIProvider

CONCEPT = "clinical research participant recruitment"
PROVIDER = os.getenv("THOUGHT_GRAPH_PROVIDER", "openai").strip().lower()
REQUEST_DELAY_SECONDS = float(os.getenv("BEHAVIOR_TEST_DELAY_SECONDS", "0"))
MODEL_DEFAULTS = {
    "openai": "gpt-5.6-luna",
    "gemini": "gemini-3.6-flash",
    "deepseek": "deepseek-v4-flash",
}


def build_provider() -> tuple[LLMProvider, str]:
    """Build the selected provider and resolve its provider-specific model."""
    try:
        default_model = MODEL_DEFAULTS[PROVIDER]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported THOUGHT_GRAPH_PROVIDER: {PROVIDER}. "
            "Use openai, gemini, or deepseek."
        ) from exc

    model = os.getenv(f"{PROVIDER.upper()}_MODEL", default_model)
    provider_classes = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
    }
    return provider_classes[PROVIDER](), model


def print_section(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    provider, model = build_provider()
    engine = ThoughtGraphEngine(provider, model=model)

    print_section("HORIZONTAL RESULT")
    print(f"Concept: {CONCEPT}")
    print(f"Provider: {PROVIDER}")
    print(f"Model: {model}")

    array = engine.generate_array_of_thoughts(CONCEPT, max_subtopics=6, max_tokens=4096)
    for index, thought in enumerate(array.thoughts, start=1):
        print(f"{index}. {thought.name}")
        print(f"   Description: {thought.description}")

    print_section("VERTICAL DIRECT-CHILD RESULTS FOR ALL HORIZONTAL THOUGHTS")
    print(f"Concept: {CONCEPT}")

    for index, parent in enumerate(array.thoughts):
        if index and REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS)
        print(f"\nParent: {parent.name}")
        children = engine.expand_subtopic(
            concept=CONCEPT,
            subtopic=parent.name,
            max_details=6,
            max_tokens=4096,
        )
        for index, child in enumerate(children, start=1):
            print(f"  {index}. {child}")


if __name__ == "__main__":
    main()
