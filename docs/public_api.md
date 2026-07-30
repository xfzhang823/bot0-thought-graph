# Public API

The stable top-level entry points are:

- `ThoughtGraphEngine` for provider-injected thought generation, expansion, indexing, and explicit saving.
- `InterviewEngine` for typed, headless interview sessions and explicit session saving.
- `InterviewCoordinator` as a thin delegation layer for applications.
- `LLMProvider` and `AsyncLLMProvider` protocols for custom providers.
- `MemoryRepository` and `JsonRepository` for optional caller-selected persistence.

Requests, models, policies, and adapter classes are available from their subpackages. Provider SDK adapters are lazy and require the `providers` extra; fake/custom providers require no SDK client construction.

The package is synchronous at its public engine boundary. It has no global clients, implicit model/provider selection, repository-root discovery, automatic persistence, or import-time network/filesystem behavior. Callers may extend it by implementing `LLMProvider` or `Repository` and injecting those objects.

Intentional differences from legacy application behavior:

- Thought-engine clustering is explicit rather than hidden in every generation call.
- Interview processing is typed and headless rather than terminal-driven.
- The migrated interview engine is synchronous.
- Persistence is optional and explicit.
- Legacy facilitator retries and file-backed conversation logging are not included.
