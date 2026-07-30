"""Public provider-injected thought-generation engine."""

from dataclasses import dataclass
from typing import Any

from bot0_thought_graph.models import IdeaClusterJSONModel, IdeaJSONModel, IndexedIdeaJSONModel
from bot0_thought_graph.providers import LLMProvider
from bot0_thought_graph.storage import Repository

from .expansion import expand_idea, expand_vertical
from .generation import generate_horizontal
from .indexing import index_idea
from .ranking import convert_clusters_to_idea, select_clusters


@dataclass(frozen=True)
class HorizontalGenerationRequest:
    idea: str
    model: str
    num_thoughts: int = 10
    num_clusters: int | None = None
    top_n: int | None = None
    temperature: float = 0.7
    max_tokens: int = 1056
    timeout: float | None = None


@dataclass(frozen=True)
class VerticalGenerationRequest:
    idea: str
    thought: str
    model: str
    progression_type: str = "implementation_steps"
    num_sub_thoughts: int = 7
    temperature: float = 0.7
    max_tokens: int = 1056
    timeout: float | None = None


class ThoughtGraphEngine:
    """Generate thought graphs in memory using an injected provider."""

    def __init__(self, provider: LLMProvider, repository: Repository[Any] | None = None) -> None:
        self.provider = provider
        self.repository = repository

    def generate(self, request: HorizontalGenerationRequest) -> IdeaJSONModel:
        """Generate horizontal thoughts, optionally followed by explicit clustering."""
        result = generate_horizontal(
            self.provider,
            idea=request.idea,
            model=request.model,
            num_thoughts=request.num_thoughts,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )
        if request.num_clusters is None and request.top_n is None:
            return result
        if request.num_clusters is None or request.top_n is None:
            raise ValueError("num_clusters and top_n must be supplied together")
        clusters = select_clusters(
            self.provider,
            result,
            model=request.model,
            num_clusters=request.num_clusters,
            top_n=request.top_n,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )
        return convert_clusters_to_idea(clusters)

    def expand(self, request: VerticalGenerationRequest):
        """Generate one vertical expansion in memory."""
        return expand_vertical(
            self.provider,
            idea=request.idea,
            thought=request.thought,
            model=request.model,
            progression_type=request.progression_type,
            num_sub_thoughts=request.num_sub_thoughts,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=request.timeout,
        )

    def expand_all(
        self,
        idea: IdeaJSONModel,
        *,
        model: str,
        progression_type: str = "implementation_steps",
        num_sub_thoughts: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1056,
        timeout: float | None = None,
    ) -> IdeaJSONModel:
        """Expand every thought in source order without persisting the result."""
        return expand_idea(
            self.provider,
            idea,
            model=model,
            progression_type=progression_type,
            num_sub_thoughts=num_sub_thoughts,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

    @staticmethod
    def index(idea: IdeaJSONModel) -> IndexedIdeaJSONModel:
        """Create deterministic zero-based indices without persistence."""
        return index_idea(idea)

    def save(self, key: str, value: Any) -> None:
        """Persist a result only through an explicitly supplied repository."""
        if self.repository is None:
            raise RuntimeError("No repository was supplied; results remain in memory")
        payload = value.model_dump() if hasattr(value, "model_dump") else value
        self.repository.save(key, payload)
