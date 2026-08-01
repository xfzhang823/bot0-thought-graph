"""Public provider-injected thought-generation engine."""

from dataclasses import dataclass
from typing import Any

from bot0_thought_graph.models import (
    IdeaClusterJSONModel,
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    Thought,
    ThoughtArray,
    ThoughtGraph,
    ThoughtNode,
)
from bot0_thought_graph.prompts import (
    CONCEPT_DETAIL_GENERATION_PROMPT,
    CONCEPT_SUBTOPIC_GENERATION_PROMPT,
)
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
    prompt_template: str | None = None


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
    prompt_template: str | None = None


class ThoughtGraphEngine:
    """Generate thought graphs in memory using an injected provider."""

    MAX_FACADE_DEPTH = 3

    def __init__(
        self,
        provider: LLMProvider,
        repository: Repository[Any] | None = None,
        *,
        model: str = "default",
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.model = self._require_text(model, "model")

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
            prompt_template=request.prompt_template,
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
            prompt_template=request.prompt_template,
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

    def generate_subtopics(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        ranked: bool = False,
        model: str | None = None,
    ) -> list[str]:
        """Generate sibling-level major dimensions for a concept."""
        return [item.name for item in self.generate_array_of_thoughts(
            concept,
            max_subtopics=max_subtopics,
            ranked=ranked,
            model=model,
        ).thoughts]

    def expand_subtopic(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int = 8,
        model: str | None = None,
    ) -> list[str]:
        """Generate direct, more-specific children of one subtopic."""
        result = self._expand_subtopic_result(
            concept,
            subtopic,
            max_details=max_details,
            model=model,
        )
        return [item.name for item in result.sub_thoughts or []]

    def generate_array_of_thoughts(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtArray:
        """Return a typed horizontal thought array for ``concept``."""
        concept = self._require_text(concept, "concept")
        max_subtopics = self._require_positive(max_subtopics, "max_subtopics")
        request = HorizontalGenerationRequest(
            idea=concept,
            model=self._resolve_model(model),
            num_thoughts=max_subtopics,
            num_clusters=max_subtopics if ranked else None,
            top_n=max_subtopics if ranked else None,
            prompt_template=CONCEPT_SUBTOPIC_GENERATION_PROMPT,
        )
        result = self.generate(request)
        return ThoughtArray(
            concept=concept,
            thoughts=[
                Thought(name=item.thought, description=item.description)
                for item in (result.thoughts or [])[:max_subtopics]
            ],
        )

    def generate_thought_graph(
        self,
        concept: str,
        *,
        depth: int = 2,
        breadth: int = 6,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtGraph:
        """Generate a bounded hierarchy: root plus ``depth`` child levels.

        ``depth=1`` generates the root and horizontal subtopics. ``depth=2``
        adds one vertical expansion under every subtopic. Each expanded node
        results in one provider call. The façade caps depth at three levels.
        """
        concept = self._require_text(concept, "concept")
        depth = self._require_positive(depth, "depth")
        breadth = self._require_positive(breadth, "breadth")
        if depth > self.MAX_FACADE_DEPTH:
            raise ValueError(f"depth must be <= {self.MAX_FACADE_DEPTH}")

        array = self.generate_array_of_thoughts(
            concept,
            max_subtopics=breadth,
            ranked=ranked,
            model=model,
        )
        root = ThoughtNode(
            name=concept,
            children=[
                ThoughtNode(name=item.name, description=item.description)
                for item in array.thoughts[:breadth]
            ],
        )
        if depth >= 2:
            for child in root.children:
                self._expand_graph_node(
                    child, concept, depth=depth, level=1, breadth=breadth, model=model
                )
        return ThoughtGraph(concept=concept, root=root, depth=depth, breadth=breadth)

    def _expand_graph_node(
        self,
        node: ThoughtNode,
        concept: str,
        *,
        depth: int,
        level: int,
        breadth: int,
        model: str | None,
    ) -> None:
        if level >= depth:
            return
        result = self._expand_subtopic_result(
            concept,
            node.name,
            max_details=breadth,
            model=model,
        )
        node.children = [
            ThoughtNode(name=item.name, description=item.description)
            for item in (result.sub_thoughts or [])[:breadth]
        ]
        for child in node.children:
            self._expand_graph_node(
                child, concept, depth=depth, level=level + 1, breadth=breadth, model=model
            )

    def _expand_subtopic_result(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int,
        model: str | None,
    ):
        concept = self._require_text(concept, "concept")
        subtopic = self._require_text(subtopic, "subtopic")
        max_details = self._require_positive(max_details, "max_details")
        return self.expand(
            VerticalGenerationRequest(
                idea=concept,
                thought=subtopic,
                model=self._resolve_model(model),
                progression_type="direct_children",
                num_sub_thoughts=max_details,
                prompt_template=CONCEPT_DETAIL_GENERATION_PROMPT,
            )
        )

    def _resolve_model(self, model: str | None) -> str:
        return self._require_text(model or self.model, "model")

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _require_positive(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value

    def save(self, key: str, value: Any) -> None:
        """Persist a result only through an explicitly supplied repository."""
        if self.repository is None:
            raise RuntimeError("No repository was supplied; results remain in memory")
        payload = value.model_dump() if hasattr(value, "model_dump") else value
        self.repository.save(key, payload)
