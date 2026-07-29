# Bot0 Thought Graph migration audit

Scope: architecture and migration risk only. No migration is implemented here.

## 1. Subsystem inventory

| Area | Responsibility |
|---|---|
| `src/thought_generation/` | Generate horizontal/vertical thoughts, validate models, read indexed thought files. |
| `src/models/` | Pydantic schemas for thoughts, indexed thoughts, evaluations, responses, users, and agent state. |
| `src/prompts/` | Prompt templates for thought generation and response evaluation. |
| `src/agents/` | Async question generation, evaluation, facilitation, reflection, state persistence, and topic exhaustion. |
| `src/pipelines/` | Thought-processing and interview orchestration; one module also embeds a FastAPI/TTS application template. |
| `src/utils/` | LLM calls/parsing, JSON/file helpers, filename generation, project-root discovery, and YouTube transcription. |
| `src/project_config.py` | Repository-root discovery and `input_output/`-based filenames/directories plus model constants. |
| `src/evals_and_comparisons/` | Similarity/evaluation experiments and comparison helpers. |
| Root Python services | Legacy OpenAI interview, resume, and LLM service entry points; separate from `src/`. |
| `VoiceAssist/` | Standalone voice/WebSocket, local Llama, vector-store, audio, PDF, and duplicate backup implementation. |
| `my-react-app/`, `index.js` | Frontend and Node service. |
| `tests/`, `sandbox/`, `src/*test*`, `src/main*` | Mixed unit/integration tests, manual runners, demos, and debugging entry points. |
| `input_output/`, `thought_generation/` | Checked-in generated JSON/state/memory artifacts used as runtime fixtures. |

## 2. Keep / Refactor / Exclude

| Decision | Candidates | Rationale |
|---|---|---|
| **Keep** | `models/thought_models.py`, `indexed_thought_models.py`, `evaluation_models.py`, `llm_response_models.py`; prompt constants; core thought reading/validation; `TopicExhaustionService`; focused state and question/evaluation behavior | Best reusable domain boundary; mostly deterministic schemas and algorithms. Preserve public behavior with tests before moving. |
| **Refactor** | `thought_generation/thought_generator.py`; `agents/*`; `pipelines/*`; `utils/llm_api_utils*.py`; `generic_utils.py`; `project_config.py`; logging; `interviewagent_xf_edit_2.py` | Valuable, but provider construction, persistence, prompts, root discovery, logging side effects, and orchestration are interleaved. Replace top-level imports with package imports and inject provider/storage/config dependencies. |
| **Refactor** | Duplicate response schemas in `openai_claude_llama_response_basemodels.py`; duplicate root-level services and VoiceAssist LLM code | Consolidate or quarantine after behavior is identified; currently multiple OpenAI/Claude/Llama implementations and global clients create drift. |
| **Exclude** | `my-react-app/`, `index.js`, HTML/CSS/assets; `VoiceAssist/` UI/audio/socket deployment code | Frontend/voice product surface, not reusable thought-graph core. Keep in a separate application repository if still needed. |
| **Exclude** | Checked-in `input_output/`, `thought_generation/*_output/`, `indexed_idea.json`, `src/testing_thoughts.json`, `my-react-app/src/*thought*.json` | Generated/user/session data; replace with small versioned fixtures or factory-generated test data. Runtime package must accept explicit paths/storage. |
| **Exclude** | `*_backup.py`, `*_SAVED.py`, `*_GOLD.py`, `interviewagent.py`, root legacy services, manual `main_*`, `sandbox/`, `remove_unwanted_packages.py`, shell startup scripts | Obsolete/experimental/deployment-specific until a behavior owner and test coverage are established. |
| **Exclude** | `.pkl`, `.wav`, `.pdf`, `.zip`, frontend binaries/assets; current tracked large artifacts | Not package code; move to external/model-data storage or a separate application artifact. |

## 3. Dependency map and risks

```text
prompts ───────────────┐
models ◄───────────────┼── thought_generation.thought_generator
                       │        ├── utils.llm_api_utils
                       │        └── file helpers/project_config
thought_reader ────────┘

models + prompts + utils.llm_api_utils_async
        ├── question_generator_async
        ├── evaluator_agent_async
        └── facilitator_agent_async
                ├── question generator + evaluator + reflection
                ├── state management + topic exhaustion
                └── provider clients

thought generation + agents + state/file helpers
        └── interview_pipeline_async
                └── manual/FastAPI entry points
```

Important observations:

- `ThoughtGenerator` directly constructs `OpenAI`/`Anthropic` clients and calls provider utilities; generation, parsing, validation, clustering, and file output are coupled.
- `utils.llm_api_utils_async` imports `utils.llm_api_utils`; both import models, while sync utilities import `project_config`. This is a dependency hub and likely cycle risk during package renaming, even where Python currently avoids a direct cycle.
- `logging_config` is imported by models and most layers and configures files at import time. `thought_generation/logging_config.py` also imports `utils.generic_utils`, creating avoidable infrastructure-to-domain coupling.
- Agents depend on concrete provider SDKs and concrete filesystem JSON state. `FacilitatorAgentAsync` constructs child agents and owns persistence/console interaction, making it difficult to reuse headlessly.
- `project_config` discovers `.git` and anchors all data to repository `input_output/`; this is a hard-coded deployment assumption. Root services additionally read `/root/backend/config.ini`, `./config.ini`, and environment variables.
- Existing imports are top-level (`from models...`, `from agents...`) and tests mutate `sys.path`; they will break unless all imports/tests are migrated together.
- The requested `C:/github/Bot0_Alpha/...` paths occur in `tests/test_question_loading.py`. No accidental `src/C:/` path is present in this checkout. Running that test on Linux would create/use an invalid platform-specific relative path and mutate test-repository state.

## 4. Target package structure

```text
src/bot0_thought_graph/
    __init__.py
    models/              # domain Pydantic models only
    prompts/             # prompt constants/rendering
    providers/           # provider protocol, OpenAI/Anthropic/local adapters, parsing
    thought_generation/  # generation services and indexed-thought readers
    interview/           # question/evaluation/facilitation/state services
    pipelines/           # thin application workflows, no SDK/client construction
    storage/             # JSON/session repositories; explicit paths or injected stores
    config.py            # typed settings; no repository-root discovery
```

Do not carry over a generic `utils` package; give each helper to `storage`, `providers`, or the owning domain. Keep web/FastAPI, voice, TTS, vector indexing, and frontend code outside this installable core.

## 5. Migration order

1. Freeze current behavior and add a clean test command; record import/API names that must remain temporarily compatible.
2. Extract/copy deterministic models and prompts into the package; add schema/serialization tests.
3. Move pure file/path-independent thought readers, indexing, clustering, and topic-exhaustion logic; inject storage paths.
4. Define a provider protocol and adapter contract; move response parsing behind it, with fake providers for tests.
5. Move question/evaluation agents, then facilitator/state orchestration, removing console, SDK, and filesystem construction from domain classes.
6. Compose thin thought-generation and interview pipelines; add compatibility wrappers only after package tests pass.
7. Migrate fixtures/config/entry points, then remove generated-data and legacy surfaces after an explicit deprecation window.

## 6. Test assessment

**Preserve:** `tests/test_topic_exhaustion_service.py`; the state/question-loading behavior in `tests/test_question_loading.py` after path repair; the async question-generation prompt/return-shape tests; model validation tests to be added from current schemas.

**Repair:** all tests that append `src` to `sys.path`, change the working directory, or patch top-level module paths; `src/test_thought_generation.py` currently patches file helpers but does not isolate the LLM client and imports `MagicMock` unused. The generator therefore can initialize a real OpenAI client/call path; a generic `MagicMock` response also does not provide a validated concrete provider response (`choices[0].message.content`). Integration tests need explicit opt-in credentials and network markers.

**Missing:** provider-contract tests using realistic OpenAI/Anthropic response fixtures; offline end-to-end thought generation; indexed JSON schema compatibility; state persistence/concurrency and restart tests; prompt rendering tests; invalid/empty/malformed provider responses; configuration/path portability; package install/import tests; dependency-cycle/import-order tests; retry/timeout/error tests.

## 7. Immediate blockers

- **Portability:** remove the two `C:/github/Bot0_Alpha/...` test paths and all `/root/backend/config.ini`, `./config.ini`, localhost, and repository-root assumptions before claiming a reusable package.
- **`src/C:/`:** not present in the current tracked checkout; add a guard against platform-specific path concatenation and inspect any external branch/artifact before migration.
- **Generated `input_output/`:** runtime and tests depend on checked-in generated JSON, state, and memory files. Replace with explicit storage interfaces and minimal fixtures.
- **Mocked OpenAI failure:** the thought-generation test does not mock client creation/provider response correctly; make provider injection mandatory for tests and use typed fake responses.
- **Large binaries:** no tracked `llvmlite.dll` was found in this checkout. Tracked binary/data artifacts do exist (`.pkl`, audio, PDF, ZIP, frontend images); remove them from package scope and establish external artifact handling.
- **Secrets/local machine:** no committed `.env`, `config.ini`, or obvious secret file was found, but multiple modules read API keys from ignored config files/environment and log key-related values. Credentials must be configuration-injected and never copied into package code/logging.
- **Packaging:** `pyproject.toml` names the project `bot0-alpha` and has no package build/entry-point configuration for `src/bot0_thought_graph`; installation metadata and dependency extras must be redesigned after boundaries are stable.

