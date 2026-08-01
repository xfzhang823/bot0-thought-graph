# Public API

The stable top-level entry points are:

- `ThoughtGraphEngine` for concept-first horizontal subtopics, vertical expansion, bounded thought graphs, provider-injected generation, indexing, and explicit saving.
- `Thought`, `ThoughtArray`, `ThoughtNode`, and `ThoughtGraph` as the structured concept-first result models.
- `InterviewEngine` for typed, headless interview sessions and explicit session saving.
- `InterviewCoordinator` as a thin delegation layer for applications.
- `LLMProvider` and `AsyncLLMProvider` protocols for custom providers.
- `MemoryRepository` and `JsonRepository` for optional caller-selected persistence.

Requests, models, policies, and adapter classes are available from their subpackages. Provider SDK adapters are lazy and require the `providers` extra; fake/custom providers require no SDK client construction.

The package is synchronous at its public engine boundary. It has no global clients, implicit model/provider selection, repository-root discovery, automatic persistence, or import-time network/filesystem behavior. Callers may extend it by implementing `LLMProvider` or `Repository` and injecting those objects.

## Concept-first workflow

```python
engine = ThoughtGraphEngine(provider, model="your-model")
subtopics = engine.generate_subtopics("Clinical research recruitment")
details = engine.expand_subtopic(
    "Clinical research recruitment",
    "Participant eligibility",
)
thought_array = engine.generate_array_of_thoughts("Clinical research recruitment")
graph = engine.generate_thought_graph(
    "Clinical research recruitment", depth=2, breadth=6
)
```

Horizontal methods produce sibling-level major dimensions. Vertical expansion produces direct, more-specific children of one subtopic. `ThoughtArray` contains the concept and typed first-level `Thought` items. `ThoughtGraph` contains the concept, a `ThoughtNode` root, and recursive child nodes. `depth=1` means root plus first-level subtopics; `depth=2` adds one vertical expansion under each subtopic. `breadth` caps generated children. Graph generation performs one provider call for the horizontal expansion plus one call per expanded node and never persists implicitly.

Set `ranked=True` on horizontal or graph methods to use the existing clustering/ranking path. Vertical expansion preserves provider order.

## Advanced typed API

The existing request-based API remains supported for explicit controls:

```python
from bot0_thought_graph.thought_generation import HorizontalGenerationRequest

result = engine.generate(
    HorizontalGenerationRequest(
        idea="embedded systems", model="your-model", num_thoughts=10
    )
)
```

Intentional differences from legacy application behavior:

- Thought-engine clustering is explicit rather than hidden in every generation call.
- Interview processing is typed and headless rather than terminal-driven.
- The migrated interview engine is synchronous.
- Persistence is optional and explicit.
- Legacy facilitator retries and file-backed conversation logging are not included.
