"""Public provider-injected thought-generation engine."""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from bot0_thought_graph.models import (
    IdeaClusterJSONModel,
    IdeaJSONModel,
    IndexedIdeaJSONModel,
    ProgressionType,
    Thought,
    ThoughtArray,
    ThoughtGraph,
    ThoughtNode,
)
from bot0_thought_graph.prompts import (
    CONCEPT_DETAIL_GENERATION_PROMPT,
    CONCEPT_SUBTOPIC_GENERATION_PROMPT,
)
from bot0_thought_graph.providers import LLMProvider, create_provider, default_model
from bot0_thought_graph.storage import Repository

from .expansion import expand_idea, expand_vertical
from .generation import generate_horizontal
from .indexing import index_idea
from .ranking import convert_clusters_to_idea, select_clusters


@dataclass(frozen=True)
class HorizontalGenerationRequest:
    """Configuration for generating sibling-level thoughts about an idea.

    A horizontal generation request asks the provider to explore an idea across
    multiple peer dimensions. The generated thoughts should generally remain at
    a similar level of abstraction rather than forming a parent-child sequence.

    Clustering and ranking are optional. To enable them, both ``num_clusters``
    and ``top_n`` must be supplied.

    Attributes:
        idea: Concept or idea to expand horizontally.
        model: Provider-specific model identifier.
        num_thoughts: Maximum number of initial thoughts to request.
        num_clusters: Number of semantic clusters to form during ranking.
            Must be supplied together with ``top_n``.
        top_n: Number of representative clusters to retain. Must be supplied
            together with ``num_clusters``.
        temperature: Sampling temperature passed to the language model.
        max_tokens: Maximum number of tokens allowed in the provider response.
        timeout: Optional provider-call timeout in seconds.
        prompt_template: Optional prompt override. When omitted, the underlying
            generation function uses its default horizontal-generation prompt.
    """

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
    """Configuration for expanding one thought into more-specific children.

    A vertical generation request starts with an idea and one selected thought,
    then asks the provider to generate a lower-level decomposition beneath that
    thought.

    Attributes:
        idea: Root concept that provides context for the expansion.
        thought: Existing thought to expand.
        model: Provider-specific model identifier.
        progression_type: Semantic relationship expected between the parent
            thought and its generated children. Supported prompt-guided values
            include ``implementation_steps``, ``simple_to_complex``,
            ``chronological``, ``problem_solution``, and
            ``implementation_steps`` and ``prerequisite_dependency``.
        num_sub_thoughts: Maximum number of child thoughts to request.
        temperature: Sampling temperature passed to the language model.
        max_tokens: Maximum number of tokens allowed in the provider response.
        timeout: Optional provider-call timeout in seconds.
        prompt_template: Optional prompt override. When omitted, the underlying
            expansion function uses its default vertical-expansion prompt.
    """

    idea: str
    thought: str
    model: str
    progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS
    num_sub_thoughts: int = 7
    temperature: float = 0.7
    max_tokens: int = 1056
    timeout: float | None = None
    prompt_template: str | None = None

    def __post_init__(self) -> None:
        """Normalize compatible raw strings to the public enum."""
        if not isinstance(self.progression_type, ProgressionType):
            object.__setattr__(self, "progression_type", ProgressionType(self.progression_type))


class _ExplorationReason(str, Enum):
    """Stable internal categories for adaptive continuation diagnostics."""

    DEPTH_LIMIT = "depth_limit"
    INSUFFICIENT_DISTINCTNESS = "insufficient_distinctness"
    INSUFFICIENT_NOVELTY = "insufficient_novelty"
    INTERNAL_CANDIDATE_LIMIT = "internal_candidate_limit"
    MATERIAL_DISTINCT = "materially_distinct"
    MEANINGFUL_CHILDREN = "meaningful_children"
    NATURAL_ENDPOINT = "natural_endpoint"
    NO_CANDIDATE = "no_candidate"
    NO_CHILDREN = "no_children"
    BRANCH_PRUNED = "branch_pruned"
    CALL_BUDGET = "call_budget"
    EXPANSION_BUDGET = "expansion_budget"
    NODE_BUDGET = "node_budget"


@dataclass(frozen=True)
class _ExplorationDecision:
    """Recorded adaptive continuation decision for diagnostics and tests."""

    axis: str
    action: str
    reason: _ExplorationReason
    level: int
    thought: str | None = None


class ThoughtGraphEngine:
    """Generate, expand, organize, and optionally persist thought structures.

    ``ThoughtGraphEngine`` is the primary public façade for exploring a concept
    as an array or hierarchy of related thoughts.

    The engine supports two complementary workflows:

    1. A concept-first façade for generating major subtopics, expanding one
       subtopic into more-specific details, producing typed thought arrays, and
       constructing bounded thought graphs.
    2. A lower-level typed API based on ``HorizontalGenerationRequest`` and
       ``VerticalGenerationRequest`` for callers that need direct control over
       model settings, prompts, progression types, clustering, or ranking.

    Horizontal generation produces sibling-level dimensions of an idea.
    Vertical generation produces more-specific children beneath a selected
    thought.

    All generation and expansion operations remain in memory. Supplying a
    repository does not enable automatic persistence; callers must invoke
    ``save`` explicitly.

    Attributes:
        provider: Language-model provider used for generation, expansion,
            clustering, and ranking.
        repository: Optional repository used only by explicit ``save`` calls.
        model: Default provider-specific model identifier used by the
            concept-first façade.
    """

    DEFAULT_FACADE_DEPTH = 2
    """Default number of generated child levels beneath the root."""

    DEFAULT_FACADE_BREADTH = 6
    """Default number of root-level horizontal thoughts retained."""

    _DEFAULT_VERTICAL_CHILDREN = 7
    """Internal child cap for new explicit horizontal/vertical graph calls."""

    MAX_FACADE_DEPTH = 8
    """Maximum number of generated child levels supported by new mode."""

    _MAX_LEGACY_DEPTH = 3
    """Maximum legacy ``depth`` retained for backward compatibility."""

    _ADAPTIVE_MAX_HORIZONTAL = 8
    """Internal guard against unbounded horizontal candidate generation."""

    _ADAPTIVE_PROFILE_OVERLAP_LIMITS = {
        "focused": 0.25,
        "balanced": 0.50,
        "rich": 0.75,
    }
    _ADAPTIVE_BRANCH_OVERLAP_LIMITS = {
        "focused": 0.05,
        "balanced": 0.25,
        "rich": 0.50,
    }

    _ADAPTIVE_MAX_PROVIDER_CALLS = 64
    """Internal profile-independent provider-call guard."""

    _ADAPTIVE_MAX_NODES = 128
    """Internal profile-independent retained-node guard."""

    _ADAPTIVE_MAX_EXPANSIONS = 64
    """Internal profile-independent expansion-attempt guard."""

    _NATURAL_ENDPOINT_TERMS = frozenset(
        {
            "completed",
            "conclusion",
            "done",
            "endpoint",
            "finished",
        }
    )
    _NATURAL_ENDPOINT_PHRASES = frozenset(
        {
            "conclusion",
            "done",
            "final answer",
            "final result",
            "final step",
            "final summary",
            "finished",
            "natural endpoint",
            "project complete",
            "work complete",
        }
    )
    _TOKEN_STOP_WORDS = frozenset(
        {"a", "an", "and", "for", "in", "of", "on", "the", "to", "with"}
    )

    def __init__(
        self,
        provider: LLMProvider | str,
        repository: Repository[Any] | None = None,
        *,
        model: str | None = None,
    ) -> None:
        """Initialize the thought-graph engine.

        Args:
            provider: Provider implementation responsible for language-model
                calls, or a supported provider name. Named providers are
                created through ``bot0_thought_graph.providers.create_provider``.
            repository: Optional persistence adapter. Results are not persisted
                unless ``save`` is called explicitly.
            model: Default model identifier used by façade methods when a
                per-call model override is not supplied. When omitted for a
                named provider, the package's provider default is used; when
                omitted for an injected provider, ``"default"`` preserves the
                existing injected-engine behavior.

        Raises:
            ValueError: If ``model`` is not a non-empty string.
        """
        if isinstance(provider, str):
            provider_name = self._require_text(provider, "provider").lower()
            self.provider = create_provider(provider_name)
            resolved_model = model if model is not None else default_model(provider_name)
        else:
            self.provider = provider
            resolved_model = model if model is not None else "default"
        self.repository = repository
        self.model = self._require_text(resolved_model, "model")
        self.last_exploration_trace: list[_ExplorationDecision] = []
        self.last_exploration_profile: str | None = None
        self._adaptive_provider_calls = 0
        self._adaptive_node_count = 0
        self._adaptive_expansion_attempts = 0
        self._adaptive_safety_stopped = False

    def generate(self, request: HorizontalGenerationRequest) -> IdeaJSONModel:
        """Generate sibling-level thoughts using the typed horizontal API.

        The method first performs horizontal thought generation. When both
        ``request.num_clusters`` and ``request.top_n`` are supplied, the
        generated thoughts are passed through the existing clustering and
        ranking pipeline.

        ``num_clusters`` and ``top_n`` must either both be omitted or both be
        supplied. Generation does not persist the result.

        Args:
            request: Complete horizontal-generation configuration, including
                the source idea, model, number of thoughts, provider settings,
                and optional ranking parameters.

        Returns:
            An ``IdeaJSONModel`` containing the generated thoughts. When
            clustering is enabled, the model contains the selected cluster
            representatives converted back into the standard idea structure.

        Raises:
            ValueError: If exactly one of ``num_clusters`` and ``top_n`` is
                supplied.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
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
        """Expand one thought using the typed vertical API.

        The selected thought is expanded within the context of the root idea.
        ``request.progression_type`` defines the intended relationship between
        the parent thought and its generated children, such as implementation
        steps, direct conceptual children, or strict prerequisites.

        This method performs one vertical expansion operation and does not
        persist the result.

        Args:
            request: Complete vertical-expansion configuration, including the
                root idea, selected thought, model, progression type, provider
                settings, and optional prompt override.

        Returns:
            The vertical-expansion result produced by ``expand_vertical``. The
            returned object includes the selected thought and its generated
            sub-thoughts.

        Raises:
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
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
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
        num_sub_thoughts: int = 5,
        temperature: float = 0.7,
        max_tokens: int = 1056,
        timeout: float | None = None,
    ) -> IdeaJSONModel:
        """Expand every top-level thought in an idea.

        Thoughts are processed in their existing source order. Each thought is
        expanded according to the requested progression type. Depending on the
        underlying implementation, expansion may require one provider call per
        top-level thought.

        The operation remains in memory and does not persist the expanded idea.

        Args:
            idea: Idea model whose top-level thoughts should be expanded.
            model: Provider-specific model identifier.
            progression_type: Semantic relationship expected between each
                parent thought and its generated children.
            num_sub_thoughts: Maximum number of children requested for each
                top-level thought.
            temperature: Sampling temperature used for provider calls.
            max_tokens: Maximum number of response tokens allowed per call.
            timeout: Optional provider-call timeout in seconds.

        Returns:
            An ``IdeaJSONModel`` containing the original thoughts and their
            generated vertical expansions.

        Raises:
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        progression_type = ProgressionType(progression_type)
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
        """Assign deterministic zero-based indices to an idea hierarchy.

        Indexing preserves the source ordering of thoughts and sub-thoughts.
        The operation is deterministic, does not call the language-model
        provider, and does not persist the result.

        Args:
            idea: Unindexed idea model.

        Returns:
            An ``IndexedIdeaJSONModel`` containing the same logical structure
            with deterministic zero-based indices.
        """
        return index_idea(idea)

    def generate_subtopics(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        ranked: bool = False,
        model: str | None = None,
    ) -> list[str]:
        """Generate major sibling-level dimensions of a concept.

        This is the simplest horizontal-expansion method. It asks the provider
        to identify broad, peer-level areas of the concept rather than
        procedural steps or lower-level details.

        When ``ranked`` is true, the generated thoughts are passed through the
        existing clustering and ranking pipeline before their names are
        returned.

        Args:
            concept: Concept to explore horizontally.
            max_subtopics: Maximum number of subtopic names to return.
            ranked: Whether to cluster and rank the generated subtopics.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A list of generated subtopic names in source or ranked order.

        Raises:
            ValueError: If ``concept`` is empty, ``max_subtopics`` is not a
                positive integer, or the resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
        return [
            item.name
            for item in self.generate_array_of_thoughts(
                concept,
                max_subtopics=max_subtopics,
                ranked=ranked,
                model=model,
            ).thoughts
        ]

    def expand_subtopic(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int = 8,
        max_tokens: int = 1056,
        model: str | None = None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
    ) -> list[str]:
        """Generate direct, more-specific children of one subtopic.

        This is the simplest vertical-expansion method. The generated details
        should remain within the context of ``concept`` while representing a
        lower level of abstraction beneath ``subtopic``.

        The method performs one provider expansion call and does not persist
        the result.

        Args:
            concept: Root concept that constrains the expansion.
            subtopic: Existing subtopic to expand vertically.
            max_details: Maximum number of direct-child names to return.
            max_tokens: Maximum number of provider response tokens.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.
            progression_type: Semantic relationship used for generated
                children. Raw strings are normalized to ``ProgressionType``.

        Returns:
            A list containing the names of the generated direct children.

        Raises:
            ValueError: If ``concept`` or ``subtopic`` is empty,
                ``max_details`` is not a positive integer, or the resolved model
                identifier is empty.
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        result = self._expand_subtopic_result(
            concept,
            subtopic,
            max_details=max_details,
            max_tokens=max_tokens,
            model=model,
            progression_type=progression_type,
        )
        return [item.name for item in result.sub_thoughts or []]

    def generate_array_of_thoughts(
        self,
        concept: str,
        *,
        max_subtopics: int = 8,
        max_tokens: int = 1056,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtArray:
        """Generate a typed horizontal array of thoughts for a concept.

        Unlike ``generate_subtopics``, which returns only names, this method
        preserves each generated thought as a public ``Thought`` object,
        including its description when one is available.

        The generated thoughts are intended to be sibling-level dimensions:
        broad areas that collectively describe the concept at a similar level
        of abstraction.

        Args:
            concept: Concept to explore horizontally.
            max_subtopics: Maximum number of thoughts included in the returned
                array.
            max_tokens: Maximum number of provider response tokens.
            ranked: Whether to cluster and rank the generated thoughts before
                constructing the array.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A ``ThoughtArray`` containing the normalized concept and its
            generated sibling-level thoughts.

        Raises:
            ValueError: If ``concept`` is empty, ``max_subtopics`` is not a
                positive integer, or the resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, or ranking exception
                raised by the underlying implementation.
        """
        concept = self._require_text(concept, "concept")
        max_subtopics = self._require_positive(max_subtopics, "max_subtopics")
        request = HorizontalGenerationRequest(
            idea=concept,
            model=self._resolve_model(model),
            num_thoughts=max_subtopics,
            max_tokens=max_tokens,
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
        concept: str | None = None,
        *,
        topic: str | None = None,
        depth: int | None = None,
        breadth: int | None = None,
        horizontal: int | None = None,
        vertical: int | None = None,
        exploration: str | None = None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
        ranked: bool = False,
        model: str | None = None,
    ) -> ThoughtGraph:
        """Generate a bounded hierarchical thought graph.

        The graph begins with ``concept`` as its root node. The first child
        level is generated horizontally as a set of sibling-level subtopics.
        Each deeper level is generated vertically by expanding each node into
        direct, more-specific children.

        Depth counts generated child levels beneath the root:

        * ``depth=1`` creates the root and its horizontal subtopics.
        * ``depth=2`` additionally expands every first-level subtopic.
        * ``depth=3`` additionally expands every second-level node.

        Legacy ``breadth`` limits the number of children retained at every
        expanded node. New callers can instead use independent
        ``horizontal`` and ``vertical`` values: ``horizontal`` limits the
        root-level peer directions, while ``vertical`` limits generated child
        levels beneath the root. New explicit calls use the internal default
        vertical child cap rather than reusing ``horizontal``.

        When no graph-shape bounds are supplied, ``exploration`` defaults to
        ``"balanced"`` and continuation is evaluated as the graph develops.
        Adaptive exploration is opt-in when a profile is supplied and cannot
        be combined with explicit or legacy graph-shape bounds.

        Explicit graph generation begins with one horizontal provider call.
        Adaptive generation may make additional bounded horizontal candidate
        calls while evaluating continuation. Each node expanded below the
        first level requires an additional vertical provider call. Provider-
        call volume can therefore grow quickly as the graph expands.

        Ranking applies only to the initial horizontal subtopics. Generated
        graphs remain in memory and are not persisted automatically.

        Args:
            concept: Root concept represented by the graph. Existing callers
                may continue to pass this positionally or by keyword.
            topic: Alias for ``concept`` intended for external callers. Only
                one of ``concept`` and ``topic`` may be supplied.
            depth: Legacy name for the number of generated child levels beneath
                the root. Must be between 1 and ``_MAX_LEGACY_DEPTH``, inclusive.
            breadth: Legacy maximum number of children retained per expanded
                node. It cannot be combined with ``horizontal`` or ``vertical``.
            horizontal: Maximum number of root-level peer directions retained.
                It cannot be combined with ``depth`` or ``breadth``.
            vertical: Maximum number of generated child levels beneath the
                root. It cannot be combined with ``depth`` or ``breadth``.
            exploration: Adaptive continuation profile: ``"focused"``,
                ``"balanced"``, or ``"rich"``. When omitted without graph
                bounds, ``"balanced"`` is used. It cannot be combined with
                ``horizontal``, ``vertical``, ``depth``, or ``breadth``.
            progression_type: Semantic relationship used for every vertical
                graph expansion. Raw strings are normalized to
                ``ProgressionType``.
            ranked: Whether to cluster and rank the first-level horizontal
                subtopics.
            model: Optional provider-specific model override. When omitted, the
                engine's default model is used.

        Returns:
            A ``ThoughtGraph`` containing the root node, generated hierarchy,
            and the resolved depth and breadth metadata. In new explicit mode,
            those metadata fields correspond to ``vertical`` and ``horizontal``.

        Raises:
            ValueError: If ``concept`` is empty, a bound is not a positive
                integer, legacy and new bounds are mixed, ``depth`` exceeds
                ``_MAX_LEGACY_DEPTH``, ``vertical`` exceeds ``MAX_FACADE_DEPTH``,
                or the resolved model identifier is empty.
            Exception: Any provider, parsing, clustering, ranking, or validation
                exception raised during graph generation.
        """
        if topic is not None:
            if concept is not None:
                raise ValueError("provide either concept or topic, not both")
            concept = topic
        concept = self._require_text(concept, "concept")
        new_bounds_supplied = horizontal is not None or vertical is not None
        legacy_bounds_supplied = depth is not None or breadth is not None
        shape_bounds_supplied = new_bounds_supplied or legacy_bounds_supplied
        if exploration is not None:
            exploration = self._require_exploration_profile(exploration)
        elif not shape_bounds_supplied:
            exploration = "balanced"

        if exploration is not None and shape_bounds_supplied:
            raise ValueError(
                "exploration cannot be combined with depth/breadth or "
                "horizontal/vertical"
            )
        if new_bounds_supplied and legacy_bounds_supplied:
            raise ValueError(
                "horizontal/vertical cannot be combined with depth/breadth"
            )

        progression_type = ProgressionType(progression_type)
        if exploration is not None:
            self.last_exploration_trace = []
            self.last_exploration_profile = exploration
            self._start_adaptive_run()
            root = self._generate_adaptive_graph(
                concept,
                exploration=exploration,
                model=model,
                progression_type=progression_type,
            )
            return ThoughtGraph(
                concept=concept,
                root=root,
                depth=max(1, self._graph_depth(root)),
                breadth=len(root.children),
            )

        self.last_exploration_trace = []
        self.last_exploration_profile = None
        self._start_adaptive_run()

        if new_bounds_supplied:
            horizontal = self._require_positive(
                horizontal if horizontal is not None else self.DEFAULT_FACADE_BREADTH,
                "horizontal",
            )
            vertical = self._require_positive(
                vertical if vertical is not None else self.DEFAULT_FACADE_DEPTH,
                "vertical",
            )
            depth = vertical
            breadth = horizontal
            vertical_child_limit = self._DEFAULT_VERTICAL_CHILDREN
        else:
            depth = self._require_positive(
                depth if depth is not None else self.DEFAULT_FACADE_DEPTH,
                "depth",
            )
            breadth = self._require_positive(
                breadth if breadth is not None else self.DEFAULT_FACADE_BREADTH,
                "breadth",
            )
            vertical_child_limit = breadth

        if new_bounds_supplied and vertical > self.MAX_FACADE_DEPTH:
            raise ValueError(f"vertical must be <= {self.MAX_FACADE_DEPTH}")
        if not new_bounds_supplied and depth > self._MAX_LEGACY_DEPTH:
            raise ValueError(f"depth must be <= {self._MAX_LEGACY_DEPTH}")

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
                    child,
                    concept,
                    depth=depth,
                    level=1,
                    vertical_child_limit=vertical_child_limit,
                    model=model,
                    progression_type=progression_type,
                )
        return ThoughtGraph(concept=concept, root=root, depth=depth, breadth=breadth)

    def _generate_adaptive_graph(
        self,
        concept: str,
        *,
        exploration: str,
        model: str | None,
        progression_type: ProgressionType,
    ) -> ThoughtNode:
        """Generate a graph by evaluating content novelty at each continuation."""
        root = ThoughtNode(name=concept)
        self._adaptive_node_count = 1
        root.children = self._generate_adaptive_horizontal(
            concept,
            exploration=exploration,
            model=model,
        )
        for child in root.children:
            if self._adaptive_safety_stopped:
                break
            self._expand_adaptive_node(
                child,
                concept,
                exploration=exploration,
                level=1,
                path=[concept, child.name],
                model=model,
                progression_type=progression_type,
            )
        return root

    def _generate_adaptive_horizontal(
        self,
        concept: str,
        *,
        exploration: str,
        model: str | None,
    ) -> list[ThoughtNode]:
        """Generate peer directions until novelty no longer clears the profile."""
        selected: list[ThoughtNode] = []
        overlap_limit = self._profile_overlap_limit(exploration)

        for _ in range(self._ADAPTIVE_MAX_HORIZONTAL):
            if self._adaptive_safety_stopped:
                break
            if not self._consume_adaptive_work(level=0):
                break
            array = self.generate_array_of_thoughts(
                concept,
                max_subtopics=1,
                ranked=False,
                model=model,
            )
            if not array.thoughts:
                self._record_exploration_decision(
                    axis="horizontal",
                    action="stop",
                    reason=_ExplorationReason.NO_CANDIDATE,
                    level=0,
                )
                break

            candidate = array.thoughts[0]
            existing_names = [item.name for item in selected]
            if not self._is_meaningful_candidate(
                candidate.name,
                existing_names,
                overlap_limit=overlap_limit,
            ):
                self._record_exploration_decision(
                    axis="horizontal",
                    action="stop",
                    reason=_ExplorationReason.INSUFFICIENT_DISTINCTNESS,
                    level=0,
                    thought=candidate.name,
                )
                break

            if self._adaptive_node_count >= self._ADAPTIVE_MAX_NODES:
                self._record_safety_stop(
                    _ExplorationReason.NODE_BUDGET,
                    level=0,
                    thought=candidate.name,
                )
                break
            selected.append(
                ThoughtNode(name=candidate.name, description=candidate.description)
            )
            self._adaptive_node_count += 1
            self._record_exploration_decision(
                axis="horizontal",
                action="continue",
                reason=_ExplorationReason.MATERIAL_DISTINCT,
                level=0,
                thought=candidate.name,
            )
        else:
            self._record_exploration_decision(
                axis="horizontal",
                action="stop",
                reason=_ExplorationReason.INTERNAL_CANDIDATE_LIMIT,
                level=0,
            )

        return selected

    def _expand_adaptive_node(
        self,
        node: ThoughtNode,
        concept: str,
        *,
        exploration: str,
        level: int,
        path: list[str],
        model: str | None,
        progression_type: ProgressionType,
    ) -> None:
        """Expand one branch while each generated level remains meaningful."""
        if level >= self.MAX_FACADE_DEPTH:
            self._record_exploration_decision(
                axis="vertical",
                action="stop",
                reason=_ExplorationReason.DEPTH_LIMIT,
                level=level,
                thought=node.name,
            )
            return
        if self._is_natural_endpoint(node.name):
            self._record_exploration_decision(
                axis="vertical",
                action="stop",
                reason=_ExplorationReason.NATURAL_ENDPOINT,
                level=level,
                thought=node.name,
            )
            return

        if not self._consume_adaptive_work(level=level, thought=node.name):
            return

        result = self._expand_subtopic_result(
            concept,
            node.name,
            max_details=self._DEFAULT_VERTICAL_CHILDREN,
            max_tokens=1056,
            model=model,
            progression_type=progression_type,
        )
        overlap_limit = self._profile_overlap_limit(exploration)
        children = []
        for item in result.sub_thoughts or []:
            candidate_context = [*path, *(child.name for child in children)]
            if self._is_meaningful_candidate(
                item.name,
                candidate_context,
                overlap_limit=overlap_limit,
            ):
                if self._adaptive_node_count >= self._ADAPTIVE_MAX_NODES:
                    self._record_safety_stop(
                        _ExplorationReason.NODE_BUDGET,
                        level=level,
                        thought=item.name,
                    )
                    break
                children.append(
                    ThoughtNode(name=item.name, description=item.description)
                )
                self._adaptive_node_count += 1

        if not children:
            reason = (
                _ExplorationReason.NO_CHILDREN
                if not result.sub_thoughts
                else _ExplorationReason.INSUFFICIENT_NOVELTY
            )
            self._record_exploration_decision(
                axis="vertical",
                action="stop",
                reason=reason,
                level=level,
                thought=node.name,
            )
            node.children = []
            return

        node.children = children
        self._record_exploration_decision(
            axis="vertical",
            action="continue",
            reason=_ExplorationReason.MEANINGFUL_CHILDREN,
            level=level,
            thought=node.name,
        )
        for child in node.children:
            if self._adaptive_safety_stopped:
                break
            if self._is_natural_endpoint(child.name):
                self._record_exploration_decision(
                    axis="vertical",
                    action="retain",
                    reason=_ExplorationReason.NATURAL_ENDPOINT,
                    level=level + 1,
                    thought=child.name,
                )
                continue
            branch_limit = self._profile_branch_overlap_limit(exploration)
            if not self._is_meaningful_candidate(
                child.name,
                path,
                overlap_limit=branch_limit,
            ):
                self._record_exploration_decision(
                    axis="vertical",
                    action="retain",
                    reason=_ExplorationReason.BRANCH_PRUNED,
                    level=level + 1,
                    thought=child.name,
                )
                continue
            self._expand_adaptive_node(
                child,
                concept,
                exploration=exploration,
                level=level + 1,
                path=[*path, child.name],
                model=model,
                progression_type=progression_type,
            )

    def _start_adaptive_run(self) -> None:
        """Reset run-local adaptive counters; explicit mode never consumes them."""
        self._adaptive_provider_calls = 0
        self._adaptive_node_count = 0
        self._adaptive_expansion_attempts = 0
        self._adaptive_safety_stopped = False

    def _consume_adaptive_work(self, *, level: int, thought: str | None = None) -> bool:
        """Reserve one provider call and expansion attempt before doing work."""
        if self._adaptive_safety_stopped:
            return False
        if self._adaptive_provider_calls >= self._ADAPTIVE_MAX_PROVIDER_CALLS:
            self._record_safety_stop(
                _ExplorationReason.CALL_BUDGET,
                level=level,
                thought=thought,
            )
            return False
        if self._adaptive_expansion_attempts >= self._ADAPTIVE_MAX_EXPANSIONS:
            self._record_safety_stop(
                _ExplorationReason.EXPANSION_BUDGET,
                level=level,
                thought=thought,
            )
            return False
        self._adaptive_provider_calls += 1
        self._adaptive_expansion_attempts += 1
        return True

    def _record_safety_stop(
        self,
        reason: _ExplorationReason,
        *,
        level: int,
        thought: str | None = None,
    ) -> None:
        if self._adaptive_safety_stopped:
            return
        self._adaptive_safety_stopped = True
        self._record_exploration_decision(
            axis="global",
            action="stop",
            reason=reason,
            level=level,
            thought=thought,
        )

    def _record_exploration_decision(
        self,
        *,
        axis: str,
        action: str,
        reason: _ExplorationReason,
        level: int,
        thought: str | None = None,
    ) -> None:
        self.last_exploration_trace.append(
            _ExplorationDecision(
                axis=axis,
                action=action,
                reason=reason,
                level=level,
                thought=thought,
            )
        )

    @classmethod
    def _profile_overlap_limit(cls, exploration: str) -> float:
        return cls._ADAPTIVE_PROFILE_OVERLAP_LIMITS[exploration]

    @classmethod
    def _profile_branch_overlap_limit(cls, exploration: str) -> float:
        return cls._ADAPTIVE_BRANCH_OVERLAP_LIMITS[exploration]

    @classmethod
    def _is_meaningful_candidate(
        cls,
        candidate: str,
        existing: list[str],
        *,
        overlap_limit: float,
    ) -> bool:
        candidate_tokens = cls._tokens(candidate)
        if not candidate_tokens:
            return False
        return all(
            cls._token_overlap(candidate_tokens, cls._tokens(item)) <= overlap_limit
            for item in existing
        )

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", value.lower())
            if token not in ThoughtGraphEngine._TOKEN_STOP_WORDS
        }

    @staticmethod
    def _token_overlap(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    @classmethod
    def _is_natural_endpoint(cls, value: str) -> bool:
        normalized = " ".join(re.findall(r"[a-z0-9]+", value.lower()))
        if normalized in cls._NATURAL_ENDPOINT_PHRASES:
            return True
        return bool(cls._tokens(value) & cls._NATURAL_ENDPOINT_TERMS)

    @staticmethod
    def _graph_depth(node: ThoughtNode) -> int:
        """Return generated child-level depth using the public graph meaning."""
        if not node.children:
            return 0
        return 1 + max(ThoughtGraphEngine._graph_depth(child) for child in node.children)

    @staticmethod
    def _require_exploration_profile(value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("exploration must be 'focused', 'balanced', or 'rich'")
        normalized = value.strip().lower()
        if normalized not in {"focused", "balanced", "rich"}:
            raise ValueError("exploration must be 'focused', 'balanced', or 'rich'")
        return normalized

    def _expand_graph_node(
        self,
        node: ThoughtNode,
        concept: str,
        *,
        depth: int,
        level: int,
        vertical_child_limit: int,
        model: str | None,
        progression_type: ProgressionType,
    ) -> None:
        """Recursively populate descendants beneath one thought-graph node.

        The method stops when ``level`` reaches ``depth``. Otherwise, it
        performs a direct-child vertical expansion, replaces ``node.children``
        with the generated children, and recursively expands each child.

        Args:
            node: Graph node whose descendants should be generated.
            concept: Root concept used to constrain every vertical expansion.
            depth: Maximum generated child depth beneath the root.
            level: Current depth of ``node`` relative to the root.
            vertical_child_limit: Internal maximum number of children retained
                for each vertical expansion.
            model: Optional provider-specific model override.

        Notes:
            This method mutates ``node.children`` in place. Each node expanded
            by this method results in one provider call.
        """
        if level >= depth:
            return
        result = self._expand_subtopic_result(
            concept,
            node.name,
            max_details=vertical_child_limit,
            max_tokens=1056,
            model=model,
            progression_type=progression_type,
        )
        node.children = [
            ThoughtNode(name=item.name, description=item.description)
            for item in (result.sub_thoughts or [])[:vertical_child_limit]
        ]
        for child in node.children:
            self._expand_graph_node(
                child,
                concept,
                depth=depth,
                level=level + 1,
                vertical_child_limit=vertical_child_limit,
                model=model,
                progression_type=progression_type,
            )

    def _expand_subtopic_result(
        self,
        concept: str,
        subtopic: str,
        *,
        max_details: int,
        max_tokens: int,
        model: str | None,
        progression_type: ProgressionType = ProgressionType.IMPLEMENTATION_STEPS,
    ):
        """Generate the typed vertical-expansion result for one subtopic.

        This helper validates the façade arguments and translates them into a
        ``VerticalGenerationRequest`` configured for the requested progression
        type.

        Args:
            concept: Root concept that constrains the expansion.
            subtopic: Parent thought to expand.
            max_details: Maximum number of direct children to request.
            model: Optional provider-specific model override.

        Returns:
            The typed vertical-expansion result returned by ``expand``.

        Raises:
            ValueError: If ``concept`` or ``subtopic`` is empty,
                ``max_details`` is not a positive integer, or the resolved model
                identifier is empty.
            Exception: Any provider, parsing, or validation exception raised by
                the underlying expansion implementation.
        """
        concept = self._require_text(concept, "concept")
        subtopic = self._require_text(subtopic, "subtopic")
        max_details = self._require_positive(max_details, "max_details")
        return self.expand(
            VerticalGenerationRequest(
                idea=concept,
                thought=subtopic,
                model=self._resolve_model(model),
                progression_type=progression_type,
                num_sub_thoughts=max_details,
                max_tokens=max_tokens,
                prompt_template=CONCEPT_DETAIL_GENERATION_PROMPT,
            )
        )

    def _resolve_model(self, model: str | None) -> str:
        """Resolve and validate the model identifier for a façade call.

        Args:
            model: Optional per-call model override.

        Returns:
            The normalized override when supplied; otherwise, the engine's
            default model identifier.

        Raises:
            ValueError: If the resolved model identifier is empty.
        """
        return self._require_text(model or self.model, "model")

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        """Validate and normalize a required text argument.

        Args:
            value: Candidate string value.
            name: Parameter name included in validation errors.

        Returns:
            The input string with surrounding whitespace removed.

        Raises:
            ValueError: If ``value`` is not a string or contains only
                whitespace.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must not be empty")
        return value.strip()

    @staticmethod
    def _require_positive(value: int, name: str) -> int:
        """Validate that a value is a positive, non-Boolean integer.

        Booleans are rejected explicitly even though ``bool`` is a subclass of
        ``int`` in Python.

        Args:
            value: Candidate integer value.
            name: Parameter name included in validation errors.

        Returns:
            The validated positive integer.

        Raises:
            ValueError: If ``value`` is Boolean, is not an integer, or is less
                than one.
        """
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
        return value

    def save(self, key: str, value: Any) -> None:
        """Persist a value through the explicitly configured repository.

        Persistence is opt-in. Generation, expansion, indexing, and graph
        construction never invoke this method automatically.

        Values exposing a Pydantic-style ``model_dump`` method are converted to
        plain Python data before being passed to the repository. Other values
        are forwarded unchanged.

        Args:
            key: Repository key under which the value should be stored.
            value: Generated result or arbitrary payload to persist.

        Raises:
            RuntimeError: If the engine was initialized without a repository.
            Exception: Any repository-specific exception raised by the save
                operation.
        """
        if self.repository is None:
            raise RuntimeError("No repository was supplied; results remain in memory")
        payload = value.model_dump() if hasattr(value, "model_dump") else value
        self.repository.save(key, payload)
