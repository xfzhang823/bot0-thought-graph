"""Small convenience functions for normal package consumers."""

from bot0_thought_graph.models import ThoughtGraph
from bot0_thought_graph.providers import LLMProvider
from bot0_thought_graph.thought_generation import ThoughtGraphEngine


def generate_thought_graph(
    topic: str,
    *,
    exploration: str = "balanced",
    provider: LLMProvider | str | None = None,
    model: str | None = None,
) -> ThoughtGraph:
    """Generate a thought graph through the canonical engine.

    Provider selection remains explicit because the package has no implicit
    provider-selection setting.  When ``provider`` is a provider name, the
    existing engine/provider architecture resolves its default model and any
    ``<PROVIDER>_MODEL`` environment override when ``model`` is omitted.
    """
    if provider is None:
        raise ValueError(
            "provider is required; pass a provider name or an LLMProvider "
            "instance"
        )

    engine = ThoughtGraphEngine(provider, model=model)
    return engine.generate_thought_graph(topic=topic, exploration=exploration)


__all__ = ["generate_thought_graph"]
