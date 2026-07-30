# Target architecture

## Purpose

`bot0-thought-graph` will provide a reusable Python package for structured thought generation and guided interviewing workflows.

## Design principles

- Keep domain models and workflows independent from applications and deployment environments.
- Make provider, storage, and configuration boundaries explicit.
- Preserve current behavior while migrating in small, tested slices.
- Keep integrations and generated artifacts outside the package core.

## Included components

The package boundary includes thought and interview domain models, prompts, provider integration boundaries, thought-generation services, interview services, thin orchestration, and optional storage implementations. Public behavior is provider-injected and headless.

## Excluded components

Frontend code, VoiceAssist, generated/runtime data, experiments, backups, and deployment-specific services remain outside the reusable package. See [excluded_components.md](excluded_components.md).

## Target package layout

```text
src/bot0_thought_graph/
    models/
    prompts/
    providers/
    thought_generation/
    interview/
    orchestration/
    storage/
```

Legacy agents, pipelines, utilities, services, and application assets remain in the repository only where compatibility or deferred migration requires them. They are not package dependencies.
