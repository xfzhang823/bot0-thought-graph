# bot0-thought-graph

**Version 0.1.0** · Python ≥ 3.12 · Pre-1.0: the documented core API is intended for reuse, but minor releases may still refine interfaces before 1.0.

`bot0-thought-graph` is a standalone Python package for structured thought generation and headless interviewing. It keeps provider access and persistence behind explicit caller-supplied interfaces: the package never constructs SDK clients implicitly, never writes files unless you call `save`, and has no import-time network or filesystem behavior.

## Capabilities

- ✨ **Concept-first façade** — `ThoughtGraphEngine.generate_subtopics()`, `expand_subtopic()`, `generate_array_of_thoughts()`, and `generate_thought_graph()` turn one concept into sibling-level subtopics, vertical detail expansions, and bounded hierarchies.
- Horizontal and vertical thought generation with an optional clustering/ranking pass (`ranked=True` or `num_clusters`/`top_n`).
- Deterministic indexing, parsing, validation, and hierarchy traversal — no provider calls involved.
- Typed interview sessions with question generation, answer evaluation, reflection, and a deterministic topic-exhaustion policy.
- ✨ **Four provider adapters** — OpenAI, Anthropic, Google Gemini, and DeepSeek — each with sync and async variants behind one `LLMProvider` protocol.
- Optional in-memory or caller-selected JSON persistence (`MemoryRepository`, `JsonRepository`).

## Installation

Requires Python 3.12 or newer.

```bash
uv add bot0-thought-graph
# Provider adapters are optional (adds openai / anthropic SDKs + python-dotenv):
uv add "bot0-thought-graph[providers]"
```

The core package depends only on `pandas>=2.2` and `pydantic>=2.9`. Provider SDK imports are lazy — `import bot0_thought_graph` works without any SDK installed; importing an adapter from `bot0_thought_graph.providers` requires the `providers` extra.

For a checkout:

```bash
uv sync
```

## Concept-first usage

The simplest workflow starts with a concept. Supply a provider implementation, or use an adapter with an explicitly constructed SDK client:

```python
from bot0_thought_graph import ThoughtGraphEngine
from bot0_thought_graph.providers import OpenAIProvider

provider = OpenAIProvider(client=my_openai_client)  # or api_key=...
engine = ThoughtGraphEngine(provider, model="your-model")
```

Tests and applications can provide any object implementing the `LLMProvider` protocol. With a fake or configured provider:

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

Graph `depth=1` returns the root concept and its first-level subtopics. `depth=2` adds one vertical expansion under each first-level subtopic. The façade bounds depth at three child levels (`MAX_FACADE_DEPTH`), caps children at `breadth`, and makes one provider call per expanded node. Set `ranked=True` on horizontal or graph methods to route the first-level subtopics through the clustering/ranking pipeline. These methods do not persist results.

## Provider support

All adapters accept either an explicitly constructed SDK client (`client=...`) or an API key (`api_key=...`); with neither, they read a key from the environment. A `.env` file in the repository or any parent directory is loaded at provider-module import without overriding existing variables.

| Provider | Status | Adapters | Environment variable | Endpoint / notes |
|----------|--------|----------|----------------------|------------------|
| OpenAI | ✅ Stable | `OpenAIProvider`, `AsyncOpenAIProvider` | `OPENAI_API_KEY` | Native OpenAI SDK |
| Anthropic | ✅ Stable | `AnthropicProvider`, `AsyncAnthropicProvider` | `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY`) | Native Anthropic SDK; content-block responses normalized |
| Google Gemini | ✨ New | `GeminiProvider`, `AsyncGeminiProvider` | `GEMINI_API_KEY` | OpenAI-compatible endpoint `https://generativelanguage.googleapis.com/v1beta/openai/` |
| DeepSeek | ✨ New | `DeepSeekProvider`, `AsyncDeepSeekProvider` | `DEEPSEEK_API_KEY` | OpenAI-compatible endpoint `https://api.deepseek.com` |

```python
from bot0_thought_graph.providers import (
    AnthropicProvider, DeepSeekProvider, GeminiProvider,
    OpenAIProvider, create_provider,
)

openai_provider = OpenAIProvider()                       # uses OPENAI_API_KEY
gemini_provider = GeminiProvider(api_key="...")          # explicit key wins
anthropic_provider = AnthropicProvider(client=my_anthropic_client)  # injected client

# Or by name:
provider = create_provider("deepseek", api_key="...")    # "openai" | "claude" | "anthropic" | "gemini" | "deepseek"
```

Model identifiers are provider-specific strings passed through unchanged; no defaults are hard-coded into the adapters. Provider calls are normalized into `GenerationResult(text, provider, model, reasoning_content)`. For OpenAI-compatible providers that return reasoning (for example DeepSeek reasoning models), the reasoning text is preserved in `reasoning_content`.

Failures are raised as typed exceptions from `bot0_thought_graph.providers`: `ProviderError` (base), `ProviderRequestError` (request rejected), and `ProviderResponseError` (response could not be normalized).

### Custom providers

`LLMProvider` is a `@runtime_checkable` protocol with a single method; any object satisfying it can be injected. The offline examples use a fake provider:

```python
from dataclasses import dataclass

from bot0_thought_graph.providers import GenerationRequest, GenerationResult

@dataclass
class FakeProvider:
    responses: list[str]

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(self.responses.pop(0), "fake", request.model)
```

An async variant, `AsyncLLMProvider`, defines `async def generate(...)` and is implemented by all `Async*` adapters. The engines themselves are synchronous at their public boundary — see [docs/public_api.md](docs/public_api.md).

## Advanced typed usage

The request-based API remains available when callers need explicit generation controls — model settings, prompt overrides, progression types, or clustering and ranking:

```python
from bot0_thought_graph.thought_generation import (
    HorizontalGenerationRequest,
    VerticalGenerationRequest,
)

result = engine.generate(
    HorizontalGenerationRequest(
        idea="embedded systems",
        model="your-model",
        num_thoughts=10,
        num_clusters=3,   # both or neither; enables clustering + ranking
        top_n=5,
    )
)  # -> IdeaJSONModel

expanded = engine.expand(
    VerticalGenerationRequest(
        idea="embedded systems",
        thought="toolchains",
        model="your-model",
        progression_type="implementation_steps",  # default; "direct_children" for the façade
        num_sub_thoughts=7,
    )
)  # -> ThoughtJSONModel
```

`num_clusters` and `top_n` must be supplied together, otherwise `ValueError` is raised. Also available: `engine.expand_all(idea_model, model=...)` (expands every top-level thought in order, one provider call each), the static `engine.index(idea_model)` (deterministic zero-based indices, no provider call), and `engine.save(key, value)` (persists only when a repository was supplied — otherwise `RuntimeError`).

## Interviewing

```python
from bot0_thought_graph import InterviewEngine
from bot0_thought_graph.interview import InterviewContext

engine = InterviewEngine(provider=my_provider, model="my-model")
session = engine.start(InterviewContext(idea_data=indexed_graph))
turn = engine.process_answer(session, "The system should make requirements explicit.")
```

`engine.start()` accepts an `InterviewContext`, or an `IndexedIdeaJSONModel` / `IdeaJSONModel` directly (unindexed ideas are indexed automatically). Each `process_answer()` call:

1. evaluates the answer against the current question (`EvaluationService`),
2. appends a typed `InterviewTurn` to the session,
3. runs the deterministic topic-exhaustion policy,
4. decides the next action (`ReflectionService`), and
5. advances, completes, or asks a follow-up question.

The returned `InterviewTurnResult` carries the evaluation, `next_question`, `topic_exhausted`, `completed`, and the `decision` (`"advance"`, `"follow_up"`, or `"complete"`) with its reason. Sessions and turn results are typed Pydantic models with no display or transport state.

Evaluation uses four criteria — `relevance`, `correctness`, `specificity`, `clarity` — scored 1–5 with explanations capped at 50 words. The default reflection policy advances when `correctness >= 4.5`; below the threshold it asks a clarifying follow-up. The `TopicExhaustionPolicy` (redundancy > 0.7 and new-information < 0.2) forces an advance when a topic is exhausted. All services are replaceable: `QuestionGenerationService`, `EvaluationService`, `ReflectionService`, and `TopicExhaustionPolicy` can be injected into `InterviewEngine`, and `InterviewPolicy` / `InterviewCoordinator` in `bot0_thought_graph.orchestration` provide a thin application-facing layer.

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
engine.save_session(session)  # writes {chosen_directory}/{session_id}.json
```

- `JsonRepository(directory)` writes `<key>.json` files atomically (temp file + `os.replace`) with sorted keys and ISO dates; keys must be plain filenames without path components.
- `MemoryRepository()` keeps values for the instance lifetime.
- `Repository[T]` (and `ThoughtRepository`) are the injectable contracts in `bot0_thought_graph.storage`; any object with `load(key)` / `save(key, value)` satisfies them.

## Models and prompts

Public models live in `bot0_thought_graph.models`. Concept-first results (`Thought`, `ThoughtArray`, `ThoughtNode`, `ThoughtGraph`) are exported at the package top level; the legacy-schema JSON models (`IdeaJSONModel`, `ThoughtJSONModel`, `SubThoughtJSONModel`, indexed variants, cluster models), evaluation models (`EvaluationCriteria`, `EvaluationJSONModel`, `QuestionAnswerPair`), and provider-neutral response models (`TextResponse`, `SubConcept`, `JSONResponse`, `TabularResponse`, `CodeResponse`) are exported from the `models` subpackage, along with `validate_thought_batch()`.

All prompt templates are public constants in `bot0_thought_graph.prompts` — horizontal/vertical generation, concept subtopic/detail prompts, clustering, and the interview evaluation and question-generation templates — and can be overridden per request via `prompt_template=`.

## Architecture

The package is organized into:

- `bot0_thought_graph.models` — deterministic Pydantic domain models
- `bot0_thought_graph.providers` — `LLMProvider`/`AsyncLLMProvider` contracts, `GenerationRequest`/`GenerationResult`, error types, lazy SDK adapters, `create_provider`
- `bot0_thought_graph.thought_generation` — `ThoughtGraphEngine`, horizontal/vertical generation, clustering and ranking, parsing, validation, indexing, in-memory readers
- `bot0_thought_graph.interview` — `InterviewEngine`, question generation, evaluation, reflection, topic-exhaustion policy, typed session state
- `bot0_thought_graph.orchestration` — thin `InterviewCoordinator` / `InterviewPolicy` delegation layer
- `bot0_thought_graph.storage` — `Repository` contract, `JsonRepository`, `MemoryRepository`
- `bot0_thought_graph.prompts` — public prompt templates
- `bot0_thought_graph.config` — optional `ProviderConfig` / `Bot0Config` frozen dataclasses (storage is deliberately never implicit)

See [docs/public_api.md](docs/public_api.md), [docs/target_architecture.md](docs/target_architecture.md), [docs/migration_audit.md](docs/migration_audit.md), and [docs/release_readiness_v0.1.0.md](docs/release_readiness_v0.1.0.md).

## Examples

Offline, deterministic, network-free — all run against a fake provider:

```bash
uv run python examples/thought_generation.py      # concept-first workflow
uv run python examples/interview.py               # one typed interview turn
uv run python examples/explicit_persistence.py    # JsonRepository in a temp dir
uv run python examples/behavior_test.py           # all façade methods end-to-end
```

`examples/support.py` defines the shared `FakeProvider` and the indexed graph fixture.

## Non-goals

Frontend, FastAPI, WebSocket, voice/audio, TTS, terminal interaction, deployment, authentication, repository-root discovery, implicit provider construction, and automatic persistence are outside this package.

🔥 **Breaking change (v0.1.0)**: the former `VoiceAssist/` prototype was extracted to the separate `voice-assist` repository and the legacy React frontend was removed from the repository. Neither is part of this package or supported as part of `bot0-thought-graph`; future voice work belongs in separate projects such as `voice-tools` and `bot0-voice-assistant`.

Legacy application modules (`src/agents`, `src/pipelines`, `src/models`, the `interviewagent*.py` scripts, etc.) remain in the repository for compatibility and deferred migration. They are not package dependencies, are excluded from the wheel (`setuptools` discovery is restricted to `bot0_thought_graph*`), and are not documented here. The migrated interview engine is synchronous; the legacy async agent modules are not part of the package.

## Development

```bash
uv sync --extra providers --extra dev
uv run python -m compileall src
uv run pytest           # testpaths=tests, pythonpath=src (legacy tests included)
uv build
```

- 53 test functions across 10 test files; six exercise the `bot0_thought_graph` package (`test_concept_first_api.py`, `test_interview_orchestration.py`, `test_package_hygiene.py`, `test_package_models_and_prompts.py`, `test_provider_storage.py`, `test_thought_generation_package.py`), the rest cover retained legacy modules.
- No SDK, network, or `.env` is required to run the package tests — they use fake providers.
- The package is import-clean: no import-time dotenv loading, provider construction, network access, or file writes (verified by `tests/test_package_hygiene.py` and the v0.1.0 release-readiness audit).
