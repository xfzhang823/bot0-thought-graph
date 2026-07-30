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

## Provider injection

The package does not load credentials or create clients during import. Supply a provider implementation or use an adapter with an explicitly constructed SDK client:

```python
from bot0_thought_graph.providers import OpenAIProvider

provider = OpenAIProvider(client=my_openai_client)
```

Tests and applications can provide any object implementing `LLMProvider`.

## Thought generation

```python
from bot0_thought_graph import ThoughtGraphEngine
from bot0_thought_graph.thought_generation import HorizontalGenerationRequest

engine = ThoughtGraphEngine(provider=my_provider)
graph = engine.generate(
    HorizontalGenerationRequest(idea="embedded systems", model="my-model")
)
```

Vertical expansion and indexing are available through `VerticalGenerationRequest`, `engine.expand()`, `engine.expand_all()`, and `engine.index()`.

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

`VoiceAssist/` is retained as legacy/reference application code. It is excluded from the distributable package and is not supported as part of `bot0-thought-graph`. Future voice work belongs in separate projects such as `voice-tools` and `bot0-voice-assistant`.

## Development

```bash
uv run python -m compileall src
uv run pytest
uv build
```

Offline examples are in `examples/` and use fake providers. The migrated package is complete for its current reusable scope; legacy application modules remain in the repository for compatibility and deferred migration, but are not package dependencies.
