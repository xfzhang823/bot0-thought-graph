# Bot0 Thought Graph migration audit

## Final package boundary

`src/bot0_thought_graph/` now contains the reusable deterministic models and prompts, provider-neutral contracts and lazy SDK adapters, optional storage, thought-generation engine, headless interview engine, and thin orchestration. It has no imports from legacy `agents`, `pipelines`, `utils`, `project_config`, `input_output`, frontend, VoiceAssist, FastAPI, or terminal code.

## Intentional semantic differences

- Thought-engine clustering is explicit through request options.
- Interview processing is typed and headless rather than console-driven.
- The migrated interview engine is synchronous.
- Persistence is optional and requires an injected repository plus an explicit save call.
- Legacy facilitator retries and file-backed conversation logging are not included.

## Retained legacy surfaces

Legacy agents, pipelines, utilities, project configuration, root services, generated data, frontend, experiments, backups, and binaries remain outside the package. The former VoiceAssist prototype was extracted to the separate `voice-assist` repository. These surfaces are application/deployment code or deferred behavior with unresolved coupling. The legacy topic-exhaustion module is now a compatibility shim to the package policy.

## Remaining technical debt

- The legacy test suite still contains application-specific tests with path mutation and hard-coded Windows fixtures; those are not package tests.
- Migrated Pydantic models emit existing class-based `Config` deprecation warnings.
- Historical generated data remains in this repository where previously tracked; VoiceAssist assets now live in the separate `voice-assist` repository and are outside this package.
- Provider adapters require the optional `providers` extra; custom/fake providers require no SDK adapter import.

## Readiness

The package is ready to serve as a standalone reusable package for its migrated scope. Application integrations and deferred legacy behavior require separate migration work.
