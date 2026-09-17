# Legacy `src/` Retirement Audit

Date: 2026-09-16  
Status: audit only; no cleanup performed

## 1. Executive summary

The canonical installed package is `src/bot0_thought_graph/`. Repository
inspection shows that it does not import `src/agents/`, `src/models/`,
`src/prompts/`, `src/pipelines/`, or `src/thought_generation/`. The canonical
package owns horizontal generation, adaptive vertical decomposition,
decomposition reflection, graph contracts, providers, graph prompts, and graph
storage.

The legacy top-level directories are parallel application infrastructure, thin
compatibility shims, or empty residue. None contains a capability that must be
migrated into the focused graph package. The old agents and interview pipelines
are conversational/application code; the old horizontal and vertical pipeline
wrappers delegate to `ThoughtGraphEngine` while adding file-oriented behavior;
the old model and prompt modules mostly re-export canonical definitions.

Recommended disposition:

- retire `src/agents/` and its async application tests once the old facilitator
  application is explicitly unsupported or moved externally;
- retire `src/pipelines/` after deciding whether the file-backed wrappers are
  still supported application entry points;
- remove the four model and two prompt compatibility shims after their legacy
  importers and parity tests are gone;
- remove the empty `src/thought_generation/` directory immediately with the
  broader legacy cleanup wave;
- remove `aiohttp`-dependent legacy tests and code together with the legacy
  async agent surface.

No legacy component is classified as a missing core capability. The only
legacy-specific behavior that remains live is `TopicExhaustionPolicy` in
`src/agents/state_transition_machine.py`, used by the old facilitator. It
should disappear with that application and must not be recreated under
`bot0_thought_graph`.

## 2. Classification summary

| Category | Count | Meaning in this audit |
|---|---:|---|
| A. DUPLICATE/SUPERSEDED | 0 | No legacy implementation is retained as a second core algorithm; the pipeline wrappers are application wrappers, not duplicate algorithms. |
| B. LEGACY APPLICATION | 11 | Agents, real legacy state, file-backed pipelines, and old interview/template application code. |
| C. CORE CAPABILITY MISSING | 0 | No evidence requires migration into the canonical graph package. |
| D. COMPATIBILITY ONLY | 9 | Empty namespace markers and model/prompt re-export shims. |
| E. ACTIVE NON-LEGACY SUPPORT | 0 | No top-level legacy surface is an active installed-package responsibility. |

Counts are for meaningful files in the audited directories, including empty
package markers as compatibility-only namespace residue. The empty
`src/thought_generation/` directory contains no source files and is counted
separately as empty residue.

## 3. Complete legacy tree inventory

### `src/agents/`

| File | Classification | Evidence and disposition |
|---|---|---|
| `agents/__init__.py` | B. LEGACY APPLICATION | Empty marker for the old agent namespace; retire with the directory. |
| `agents/evaluator_agent_async.py` | B. LEGACY APPLICATION | Async answer evaluator that constructs SDK clients and uses legacy models/prompts/utilities; unrelated to decomposition reflection. Retire or move externally with the facilitator application. |
| `agents/facilitator_agent_async.py` | B. LEGACY APPLICATION | File-backed/conversational facilitator coordinating legacy evaluator, question generator, state manager, and topic exhaustion. No canonical graph consumer requires it. Retire or move externally. |
| `agents/question_generator_async.py` | B. LEGACY APPLICATION | Async interview question generation with retrying provider calls; not reusable graph generation. Retire or move externally. |
| `agents/state_management.py` | B. LEGACY APPLICATION | File-backed user/session state for the old conversational agent; uses `models.user_state_models` and legacy utilities. Retire with the application. |
| `agents/state_transition_machine.py` | B. LEGACY APPLICATION | Self-contained `ConversationMetrics` and `TopicExhaustionPolicy` retained only for `facilitator_agent_async.py`. Retire with the facilitator; do not move into core. |

### `src/models/`

| File | Classification | Evidence and disposition |
|---|---|---|
| `models/__init__.py` | D. COMPATIBILITY ONLY | Empty legacy namespace marker. |
| `models/evaluation_models.py` | D. COMPATIBILITY ONLY | Re-exports `bot0_thought_graph.models.evaluation_models`; no unique model definitions. Remove after legacy importers and parity tests migrate. |
| `models/indexed_thought_models.py` | D. COMPATIBILITY ONLY | Re-exports canonical indexed graph models. Remove after legacy importers migrate. |
| `models/llm_response_models.py` | D. COMPATIBILITY ONLY | Re-exports canonical response models. Remove after legacy importers migrate. |
| `models/thought_models.py` | D. COMPATIBILITY ONLY | Re-exports canonical thought models. Remove after legacy importers migrate. |
| `models/user_state_models.py` | B. LEGACY APPLICATION | Real user/session state models used only by `agents/state_management.py`; not graph-domain models. Retire with the old application. |

### `src/prompts/`

| File | Classification | Evidence and disposition |
|---|---|---|
| `prompts/__init__.py` | D. COMPATIBILITY ONLY | Empty legacy namespace marker. |
| `prompts/evaluation_prompt_templates.py` | D. COMPATIBILITY ONLY | Re-exports canonical prompt constants; legacy agents import it. Remove when those agents disappear. |
| `prompts/thought_generation_prompt_templates.py` | D. COMPATIBILITY ONLY | Re-exports canonical graph-generation prompts; no unique prompt ownership. Remove when legacy pipeline/util imports disappear. |

### `src/pipelines/`

| File | Classification | Evidence and disposition |
|---|---|---|
| `pipelines/__init__.py` | D. COMPATIBILITY ONLY | Empty legacy namespace marker. |
| `pipelines/horizontal_thoughts_pipeline.py` | B. LEGACY APPLICATION | File-backed wrapper around canonical `ThoughtGraphEngine.generate()` with legacy provider constants, clustering ratios, and utility JSON persistence. Retire rather than create a canonical pipelines namespace. |
| `pipelines/vertical_thoughts_pipeline.py` | B. LEGACY APPLICATION | File-backed wrapper around canonical `ThoughtGraphEngine.expand_all()` with legacy configuration and utilities. Retire rather than migrate. |
| `pipelines/thought_processing_pipeline.py` | B. LEGACY APPLICATION | File-backed/printing wrapper around canonical readers plus legacy utilities. Retire or move externally if the old data-inspection workflow remains needed. |
| `pipelines/interview_pipeline_async.py` | B. LEGACY APPLICATION | Async interview entry point around `agents.FacilitatorAgentAsync`, legacy state, and file paths. Retire with the old interview application. |
| `pipelines/interviewing_pipeline_template_async.py` | B. LEGACY APPLICATION | Standalone FastAPI/TTS/conversation prototype with hard-coded keys and application state; not graph-core. Retire, not migrate. |

### `src/thought_generation/`

This directory contains no source files. The canonical implementation is
`src/bot0_thought_graph/thought_generation/`. The empty directory is stale
parallel namespace residue and can disappear without migration.

## 4. Dependency analysis

### Canonical package to legacy surfaces

No imports from `src/bot0_thought_graph/` resolve to any audited legacy
surface. Its relevant imports are package-qualified under
`bot0_thought_graph.models`, `.prompts`, `.providers`, `.storage`,
`.reflection`, and `.thought_generation`, plus standard library and declared
dependencies.

This was verified by repository search and direct inspection of the canonical
imports. In particular, the adaptive engine imports decomposition from
`bot0_thought_graph.reflection`, not from a legacy namespace.

Therefore deleting legacy source cannot affect the installed package's import
path or graph-generation runtime. Setuptools discovery is restricted to
`bot0_thought_graph*`, so the legacy top-level packages are not included in the
installed wheel.

### Legacy agents inbound/outbound map

| Component | Inbound callers | Outbound dependencies | Canonical replacement |
|---|---|---|---|
| `evaluator_agent_async.py` | `facilitator_agent_async.py`, legacy tests | `aiohttp`, async SDKs, legacy models/prompts/utils | Core has synchronous provider-injected answer-independent graph generation and decomposition reflection; answer evaluation is not graph-core. |
| `facilitator_agent_async.py` | `pipelines/interview_pipeline_async.py`, legacy support scripts | evaluator/question agent, state manager, legacy models/utils, async SDKs, `TopicExhaustionService` | No migration; external interview/application ownership if still wanted. |
| `question_generator_async.py` | facilitator, two async question tests | async SDKs, `aiohttp` transitively through async utilities, legacy prompts/models | No migration; external interview/application ownership if still wanted. |
| `state_management.py` | facilitator, legacy support/tests | `models.user_state_models`, legacy file utilities | No migration; external application state. |
| `state_transition_machine.py` | facilitator, `test_topic_exhaustion_legacy.py` | standard library only after Phase C | Retire with legacy facilitator; no core equivalent needed. |

The old agents form a partially runnable application architecture, but not an
installed product surface. They require legacy modules, configuration, file
paths, SDKs, and optional dependencies; the facilitator is only reached through
legacy pipeline/script paths. No external non-legacy caller was found.

### Legacy models and prompts

Four legacy model files and two prompt files are exact-style re-export shims to
canonical package definitions. The parity tests confirm identity, not
independent behavior. Their consumers are legacy agents/utilities and
`tests/test_package_models_and_prompts.py`.

`user_state_models.py` is different: it defines old conversation state and has
no canonical replacement because it is not a graph-domain contract. It should
be deleted with the old agents, not migrated into `bot0_thought_graph.models`.

### Legacy pipelines

The horizontal and vertical pipelines do call the canonical engine, but add:

- legacy `project_config` model/path constants;
- file existence and overwrite rules;
- `utils` JSON read/write helpers;
- old clustering ratios and naming conventions; and
- command/script-oriented logging.

They do not own a second graph algorithm. Their eventual deletion will remove a
legacy file-backed façade, not graph-generation capability. The processing
pipeline similarly wraps canonical readers while retaining printing and legacy
file utility dependencies.

The interview pipeline and template are application code. The template also
owns unrelated FastAPI/TTS prototype behavior and should not be migrated.

## 5. Aiohttp dependency analysis

`aiohttp` is imported directly by:

- `src/agents/evaluator_agent_async.py`; and
- `src/utils/llm_api_utils_async.py`, which is used by the evaluator and question
  generator.

The failing tests import `agents.question_generator_async`, which reaches the
legacy async utility and fails collection because `aiohttp` is unavailable:

- `tests/test_question_generator_async.py`;
- `tests/test_question_generator_async_integration.py`.

The canonical `bot0_thought_graph` package does not import or require
`aiohttp`. Its provider-neutral synchronous/async protocols and installed core
dependencies are separate from these old utilities. The two tests exercise
legacy interview question generation, not a capability that should survive in
the graph package. When the legacy agents/pipelines are retired, these tests and
the associated aiohttp-dependent code can disappear together. No dependency
was installed for this audit.

## 6. Tests disposition

| Tests | Classification | Recommended disposition |
|---|---|---|
| `test_adaptive_decomposition_integration.py` | Canonical core test | Retain unchanged in the graph package. It protects adaptive vertical behavior. |
| `test_reflection_decomposition.py` | Canonical core test | Retain; it uses `bot0_thought_graph.reflection`. |
| `test_reflection_package_boundary.py` | Canonical core/boundary test | Retain interview-absence and core-reflection assertions. |
| `test_concept_first_api.py`, `test_thought_generation_package.py`, `test_behavior_test.py` | Canonical core tests | Retain. |
| `test_package_models_and_prompts.py` | Canonical core plus compatibility test | Retain canonical assertions; remove legacy shim identity assertions after the shims are deleted. |
| `test_package_hygiene.py`, `test_provider_storage.py` | Canonical core tests | Retain. |
| `test_topic_exhaustion_legacy.py` | Legacy application test | Remove with `src/agents/state_transition_machine.py`; it protects no core behavior. |
| `test_interviewagent_support.py` | Legacy application test | Remove with the old `interviewagent_support` application module. |
| `test_question_generator_async.py` | Legacy application test | Remove with legacy async question generation; currently blocked by missing `aiohttp`. |
| `test_question_generator_async_integration.py` | Legacy application test | Remove with legacy async question generation; currently blocked by missing `aiohttp`. |

No legacy test is evidence that the corresponding implementation belongs in the
canonical package. The canonical graph tests, especially adaptive decomposition
tests, are the behavior protection required during cleanup.

## 7. Scripts, examples, and entry points

There are no `[project.scripts]` entry points in `pyproject.toml`. Setuptools
includes only `bot0_thought_graph*`; the legacy packages are not installed as
package modules.

| Surface | Classification | Disposition |
|---|---|---|
| `examples/behavior_test.py`, `examples/behavior_test_adaptive.py`, `examples/thought_generation.py` | Canonical core examples | Retain; they use `ThoughtGraphEngine` and package reflection behavior. |
| `src/run_thought_generation_pipeline.py` | Legacy application entry script | Retire eventually; it invokes file-backed legacy pipeline wrappers even though those wrappers call the canonical engine. It is not needed by package consumers. |
| `src/main_walid.py` | Legacy pipeline script | Retire eventually with pipeline wrappers. |
| `src/main.py` | Legacy/incomplete application entry point | `main()` is empty and imports the old interview pipeline; retire. |
| `src/run_interview_pipeline.py` | Legacy interview entry script | Retire with the old interview application. |
| `examples/support.py` | Canonical test/example support | Retain; it supplies canonical fake-provider fixtures. |

The old scripts are not package entry points and do not affect installed-package
behavior. Documentation should stop presenting them as supported workflows when
the corresponding cleanup wave lands.

## 8. Capabilities requiring migration

No capability genuinely requires migration into the canonical graph package.

Capabilities already canonical and therefore not candidates for legacy
migration:

- horizontal thought generation;
- vertical thought generation;
- adaptive decomposition and decomposition reflection;
- graph/domain models;
- provider contracts and adapters;
- graph-owned prompts;
- graph readers and persistence.

Capabilities that may remain useful only outside this repository/package:

- conversational question generation;
- answer evaluation and interview policy;
- facilitator/session state management;
- topic exhaustion for conversations;
- file-backed application pipelines;
- FastAPI/TTS prototype behavior.

These belong in an external application if still supported. No
`bot0_thought_graph/agents/` or `bot0_thought_graph/pipelines/` namespace should
be created.

## 9. Exact blockers to deleting each legacy namespace

### `src/agents/`

The only live repository consumers are the legacy facilitator/pipeline paths,
legacy async tests, and legacy support modules. Deletion requires retiring or
moving that old application and removing its tests. It does not affect the
installed graph package.

### `src/models/`

The four re-export shims are consumed by legacy agents/utilities and the model
parity test. `user_state_models.py` is consumed by `agents/state_management.py`.
Delete after the agent/application wave and after canonical parity tests no
longer import the shims.

### `src/prompts/`

The two re-export shims are consumed by legacy agents/utilities and parity tests.
Delete after legacy importers and compatibility assertions disappear.

### `src/pipelines/`

The thought pipelines are imported by legacy run scripts and the interview
pipeline is imported by the legacy interview runner and `src/main.py`. Decide
whether those scripts are retired or moved externally, then delete the whole
directory. No canonical package import requires it.

### `src/thought_generation/`

No source-file blocker exists. Remove the empty directory with the first safe
legacy cleanup wave.

## 10. Proposed cleanup waves

### Wave 1: remove namespace residue and obsolete compatibility claims

- confirm no supported importer remains;
- remove the empty `src/thought_generation/` directory;
- remove empty `__init__.py` markers when their directories are deleted;
- remove model/prompt shims only after the legacy importer search is clean;
- update parity tests to canonical imports.

### Wave 2: retire legacy interview/facilitator application

- retire or explicitly externalize `src/agents/`;
- retire `src/pipelines/interview_pipeline_async.py` and
  `interviewing_pipeline_template_async.py`;
- remove legacy async-agent tests and the `aiohttp`-dependent code;
- remove `state_transition_machine.py` and its topic-exhaustion test with the
  facilitator, unless an external application takes ownership.

### Wave 3: retire file-backed thought pipelines

- remove or explicitly archive horizontal, vertical, and processing wrappers;
- retire `src/run_thought_generation_pipeline.py`, `src/main_walid.py`, and the
  incomplete `src/main.py`;
- ensure users use `ThoughtGraphEngine` and canonical examples instead.

### Wave 4: repository validation and documentation

- remove stale legacy references from active README/API documentation;
- retain historical audits with clear historical status;
- verify packaging contains only the canonical package;
- run canonical tests, imports, compile checks, and repository searches.

The waves should not be merged into one broad refactor. Each wave should first
verify its exact inbound references and preserve the canonical graph test
surface.

## 11. Deletion criteria

Legacy cleanup is complete when:

- canonical package source has no imports from legacy top-level namespaces;
- no supported script, example, or test imports the deleted namespace;
- canonical package installation and clean root import succeed without legacy
  modules or `aiohttp`;
- canonical model/prompt tests import package-owned definitions directly;
- graph generation and decomposition tests pass unchanged in semantics;
- horizontal/vertical generation, recursion, guards, retention, profiles,
  prompts, providers, budgets, and fallback behavior are unchanged;
- active documentation describes only the graph-focused package;
- any externally retained interview/application code has an explicit owner;
- legacy application tests are either moved with that owner or intentionally
  removed.

## 12. Risks to graph behavior

Legacy cleanup must not alter the canonical graph path. Specific risks are:

- mistaking pipeline wrappers for graph algorithms and changing engine calls;
- deleting canonical model/prompt implementations instead of only the shims;
- changing provider defaults or environment loading while removing legacy
  configuration imports;
- removing files referenced by adaptive decomposition tests or examples;
- accidentally changing `ThoughtGraphEngine` imports during package thinning.

The safe boundary is to leave all code under
`src/bot0_thought_graph/{thought_generation,reflection,providers,models,prompts,storage}`
unchanged and remove only proven legacy callers/wrappers around it.

## 13. Expected final repository/package shape

Installed package:

```text
src/bot0_thought_graph/
├── thought_generation/
├── reflection/
├── providers/
├── models/
├── prompts/
├── storage/
├── config.py
└── __init__.py
```

The repository may retain separately owned application projects or archived
historical data outside the installed package, but it should not retain
parallel `src/agents/`, `src/pipelines/`, `src/models/`, `src/prompts/`, or
`src/thought_generation/` implementations once their consumers are retired.

## 14. Unresolved questions

1. Is the old async facilitator still an intentionally supported application,
   or can `src/agents/` and its tests be retired in one wave?
2. Should file-backed thought-generation pipelines be archived for historical
   reproducibility or deleted outright?
3. Should legacy model/prompt shims receive a short deprecation window even
   though they are outside the installed package?
4. Which external project, if any, will own conversational interview behavior?
5. Are any operational users invoking the `src/run_*.py` scripts outside this
   repository? Repository search cannot establish human usage.

## Conclusion

The canonical `bot0_thought_graph` package has no dependency on the audited
legacy `src` surfaces. No missing graph-core capability was found. The old
agents and interview pipelines are legacy application code; the old models and
prompts are compatibility shims; the old thought-generation directory is empty;
and the thought pipeline wrappers are superseded application façades around the
canonical engine.

All audited legacy directories can ultimately disappear, subject only to an
explicit decision about unsupported/external legacy application usage and the
migration or removal of its tests and scripts. The cleanup described by this
audit has now been executed.

## Retirement completion note

The legacy `src/agents/`, `src/models/`, `src/prompts/`, `src/pipelines/`, and
empty `src/thought_generation/` surfaces are gone. Their legacy-only runners,
utilities, interview helpers, and async tests were also removed. The canonical
package was not changed in responsibility or behavior. The old
`TopicExhaustionPolicy` was retired with its legacy facilitator rather than
being added to the graph package.
