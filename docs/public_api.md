# Public API

The stable top-level entry points are:

- `ThoughtGraphEngine` for concept-first horizontal subtopics, vertical expansion, bounded thought graphs, named-provider or provider-injected generation, indexing, and explicit saving.
- `Thought`, `ThoughtArray`, `ThoughtNode`, and `ThoughtGraph` as the structured concept-first result models, plus the `ProgressionType` vertical-progression enum.
- `InterviewEngine` for typed, headless interview sessions and explicit session saving.
- `LLMProvider` and `AsyncLLMProvider` protocols for custom providers.
- `MemoryRepository` and `JsonRepository` for optional caller-selected persistence.

Requests, models, policies, and adapter classes are available from their subpackages. Provider SDK adapters are lazy and require the `providers` extra; fake/custom providers require no SDK client construction.

The package root no longer re-exports the thin interview controller/policy wrappers. They remain available from the `bot0_thought_graph.interview` and `bot0_thought_graph.orchestration` submodules for compatibility, but they are not part of the canonical top-level API.

The package is synchronous at its public engine boundary. It has no global clients, repository-root discovery, automatic persistence, or import-time network/filesystem behavior. Callers may extend it by implementing `LLMProvider` or `Repository` and injecting those objects.

## External consumer workflow

The canonical external API is the existing `ThoughtGraphEngine` façade:

```python
from bot0_thought_graph import ThoughtGraphEngine

generator = ThoughtGraphEngine(
    provider="deepseek",
    model="deepseek-v4-flash",
)

graph = generator.generate_thought_graph(
    topic="clinical research participant recruitment",
    depth=3,
    breadth=5,
)
```

`provider` accepts `"openai"`, `"gemini"`, `"deepseek"`, or `"anthropic"`.
Named providers are created through the existing provider factory. Set
`model=None` to use the package default, with `<PROVIDER>_MODEL` taking
precedence. Defaults are resolved by `bot0_thought_graph.providers.default_model(provider)`:
OpenAI `gpt-5.6-luna`, Gemini `gemini-3.6-flash`, DeepSeek `deepseek-v4-flash`,
Anthropic `claude-3-5-sonnet-20241022`. The returned value is always the
package-owned `ThoughtGraph` model, independent of the provider SDK.

`horizontal` is the maximum number of root-level peer directions retained;
`vertical` is the maximum number of generated child levels beneath the root.
`vertical=1` returns the root plus its first horizontal layer; `vertical=2`
adds one vertical expansion beneath each first-level thought. Explicit
horizontal and vertical values are independent, and the horizontal value is
not reused as the vertical child-count limit. The legacy `depth=` and
`breadth=` arguments remain supported and cannot be mixed with the new names.
Vertical values are bounded by `ThoughtGraphEngine.MAX_FACADE_DEPTH`. The
`topic=` parameter is canonical; the existing `concept=` parameter remains
supported as an alias (supply only one). Vertical expansion in
`generate_thought_graph()` accepts `progression_type=` (default
`ProgressionType.IMPLEMENTATION_STEPS`). Results use Pydantic's standard
`model_dump()` and `model_dump_json()` serialization.

Direct provider-object injection remains supported:

```python
engine = ThoughtGraphEngine(provider, model="your-model")
```

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
    "Clinical research recruitment", horizontal=2, vertical=8
)
```

Horizontal methods produce sibling-level major dimensions. Vertical expansion
produces direct, more-specific children of one subtopic. `ThoughtArray`
contains the concept and typed first-level `Thought` items. `ThoughtGraph`
contains the concept, a `ThoughtNode` root, and recursive child nodes.
`vertical=1` means root plus first-level subtopics; `vertical=2` adds one
vertical expansion under each subtopic. `horizontal` caps root-level peer
directions, while explicit vertical mode uses an independent internal child
cap. Graph generation performs one provider call for the horizontal expansion
plus one call per expanded node and never persists implicitly.

Set `ranked=True` on horizontal or graph methods to use the existing clustering/ranking path. `expand_subtopic()` and `generate_thought_graph()` accept `progression_type=` (a `ProgressionType` member or its string value; default `ProgressionType.IMPLEMENTATION_STEPS`) to select the parent→child semantic relationship. `ProgressionType` (`implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, `prerequisite_dependency`) is exported from `bot0_thought_graph` and `bot0_thought_graph.models`. Vertical expansion preserves provider order.

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
