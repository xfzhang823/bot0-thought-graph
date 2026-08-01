# bot0-thought-graph

`bot0-thought-graph` is a standalone Python package for structured thought generation and headless interviewing. It keeps provider access and persistence behind explicit caller-supplied interfaces.

## Capabilities

- Horizontal and vertical thought generation.
- Deterministic indexing, parsing, validation, and hierarchy traversal.
- Typed interview sessions with question generation, answer evaluation, reflection, and topic-exhaustion policy.
- Optional in-memory or caller-selected JSON persistence.

## Installation

Requires Python 3.12 or newer. This project is pre-1.0: the documented core API is intended for reuse, but minor releases may still refine interfaces before 1.0.

```bash
uv add bot0-thought-graph
# Provider adapters are optional:
uv add "bot0-thought-graph[providers]"
```

For a checkout:

```bash
uv sync
```

## Concept-first usage

The simplest workflow starts with a concept. `ThoughtGraphEngine` performs horizontal expansion into sibling-level subtopics, vertical expansion into direct children, and bounded graph construction. Supply a provider implementation or use an adapter with an explicitly constructed SDK client:

```python
from bot0_thought_graph.providers import OpenAIProvider

provider = OpenAIProvider(client=my_openai_client)
engine = ThoughtGraphEngine(provider, model="your-model")
```

Tests and applications can provide any object implementing `LLMProvider`. With a fake or configured provider:

```python
from bot0_thought_graph import ThoughtGraphEngine

engine = ThoughtGraphEngine(provider, model="your-model")
subtopics = engine.generate_subtopics("Clinical research recruitment")
details = engine.expand_subtopic(
    concept="Clinical research recruitment",
    subtopic="Participant eligibility",
)
thought_array = engine.generate_array_of_thoughts("Clinical research recruitment")
graph = engine.generate_thought_graph(
    "Clinical research recruitment",
    depth=2,
    breadth=6,
)
```

`generate_subtopics()` and `generate_array_of_thoughts()` perform horizontal expansion: they return distinct major dimensions at a similar level of abstraction. `expand_subtopic()` performs one-level vertical expansion: it returns more-specific direct children of one selected subtopic. The convenience list methods return `list[str]`; structured methods return `ThoughtArray` and `ThoughtGraph`.

Graph `depth=1` returns the root concept and its first-level subtopics. `depth=2` adds one vertical expansion under each first-level subtopic. The façade bounds depth at three child levels, caps children at `breadth`, and makes one provider call per expanded node. These methods do not persist results.

## Advanced typed usage

The request-based API remains available when callers need explicit generation controls:

```python
from bot0_thought_graph.thought_generation import HorizontalGenerationRequest

result = engine.generate(
    HorizontalGenerationRequest(
        idea="embedded systems",
        model="your-model",
        num_thoughts=10,
    )
)
```

Vertical expansion and indexing remain available through `VerticalGenerationRequest`, `engine.expand()`, `engine.expand_all()`, and `engine.index()`.

## Interviewing

```python
from bot0_thought_graph import InterviewEngine
from bot0_thought_graph.interview import InterviewContext

engine = InterviewEngine(provider=my_provider, model="my-model")
session = engine.start(InterviewContext(idea_data=indexed_graph))
turn = engine.process_answer(session, "The system should make requirements explicit.")
```

Sessions and turn results are typed and contain no display or transport state.

## Explicit persistence

No files are written by default. Persistence requires both a repository and an explicit call:

```python
from bot0_thought_graph import InterviewEngine, JsonRepository

engine = InterviewEngine(
    provider=my_provider,
    model="my-model",
    repository=JsonRepository(chosen_directory),
)
session = engine.start(context)
engine.save_session(session)
```

## Architecture

The package is organized into models, prompts, provider contracts/adapters, thought generation, interview services, thin orchestration, and optional storage. See [docs/public_api.md](docs/public_api.md) and [docs/target_architecture.md](docs/target_architecture.md).

## Non-goals

Frontend, FastAPI, WebSocket, voice/audio, TTS, terminal interaction, deployment, authentication, repository-root discovery, implicit provider construction, and automatic persistence are outside this package.

The former `VoiceAssist/` prototype was extracted to the separate `voice-assist` repository. It is not part of this package and is not supported as part of `bot0-thought-graph`. Future voice work belongs in separate projects such as `voice-tools` and `bot0-voice-assistant`.

## Development

```bash
uv run python -m compileall src
uv run pytest
uv build
```

Offline examples are in `examples/` and use fake providers. The migrated package is complete for its current reusable scope; legacy application modules remain in the repository for compatibility and deferred migration, but are not package dependencies.
