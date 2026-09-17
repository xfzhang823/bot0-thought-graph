# Canonical Interview Package Extraction Audit

Date: 2026-09-16  
Status: architecture audit; no extraction performed

## 1. Executive summary

The canonical interview subsystem is isolated from the reusable graph-generation
core after Phase A. No imports from `thought_generation`, `reflection`,
`providers`, `models`, or `storage` resolve into
`bot0_thought_graph.interview`.

The interview tree is therefore removable from the runtime core only after its
remaining consumers are moved, removed, or deliberately retained as external
compatibility consumers. The main in-repository blockers are:

1. the lazy root compatibility export `from bot0_thought_graph import
   InterviewEngine`;
2. `bot0_thought_graph.orchestration.coordinator`, which is package code but is
   itself interview-specific and imports interview types;
3. interview-specific tests and examples;
4. the legacy `src/agents/state_transition_machine.py` compatibility import for
   `TopicExhaustionPolicy`.

The Phase A reflection shims are not required by core code. They can disappear
when `interview/` is removed, provided callers using the old interview
reflection import path have migrated. The decomposition implementation itself
must remain at package-level `bot0_thought_graph.reflection`.

`InterviewEngine` can ultimately disappear from the root API. A temporary
deprecation period is safer than immediate removal because the root export is
currently intentionally preserved and two examples import it directly.

The only repository change for this audit is this document.

## 2. Complete canonical interview tree inventory

| File | Capability | Classification | Extraction disposition |
|---|---|---|---|
| `interview/__init__.py` | Public interview namespace and exports | B. INTERVIEW/APPLICATION | Move the public surface to the consuming interview package; remove from the graph package after consumers migrate. |
| `interview/engine.py` | In-memory interview lifecycle, answer processing, question/evaluation/reflection coordination, optional session save | B. INTERVIEW/APPLICATION | Move as the main external interview/application service. |
| `interview/models.py` | Interview context, session, turn, result, metadata, and interview reflection decision models | B. INTERVIEW/APPLICATION | Move with the interview service. Keep graph models sourced from `bot0_thought_graph.models`. |
| `interview/question_generation.py` | Initial and follow-up interview question generation | B. INTERVIEW/APPLICATION | Move with interview question-generation capability. |
| `interview/state.py` | Cursor validation and next interview topic location | B. INTERVIEW/APPLICATION | Move with interview orchestration/state. |
| `interview/topic_exhaustion.py` | Conversation redundancy/new-information exhaustion policy | B. INTERVIEW/APPLICATION | Move with interview policy. |
| `interview/evaluation.py` | Compatibility import for answer `EvaluationService` | D. COMPATIBILITY ONLY | Remove after callers use the external interview package’s answer-evaluation API. |
| `interview/reflection/__init__.py` | Interview reflection exports plus decomposition compatibility exports | D. COMPATIBILITY ONLY | Keep only until old reflection imports migrate; interview-specific exports move externally. |
| `interview/reflection/answer_evaluation.py` | Question-answer quality evaluation | B. INTERVIEW/APPLICATION | Move to the external interview package. It is not graph decomposition reflection. |
| `interview/reflection/policy.py` | Converts answer quality into follow-up/advance/complete action | B. INTERVIEW/APPLICATION | Move to the external interview package. |
| `interview/reflection/decomposition.py` | Re-export of package-level decomposition evaluator | D. COMPATIBILITY ONLY | Delete with the interview namespace after old imports migrate. The implementation is owned by `bot0_thought_graph.reflection`. |
| `interview/reflection/shared.py` | Re-export of package-level structured reflection helper | D. COMPATIBILITY ONLY | Delete with the interview namespace after old imports migrate. Core shared plumbing remains package-level. |

There are no obsolete implementation files in the canonical interview tree at
the time of this audit. The compatibility files are no longer independently
needed, but are classified as compatibility-only rather than obsolete because
they still preserve supported import paths.

## 3. Inbound dependency map

Inbound references were searched across package source, legacy source, tests,
examples, scripts, documentation, and packaging configuration.

### Canonical package source

| Consumer | Imported capability | Consumer class | Extraction action |
|---|---|---|---|
| `src/bot0_thought_graph/__init__.py` | Lazy `InterviewEngine` via `__getattr__` | Compatibility/public API | Remove the root export, or deprecate it first and then remove it when the external package is available. |
| `src/bot0_thought_graph/orchestration/coordinator.py` | `InterviewContext`, `InterviewEngine`, `InterviewSession`, `InterviewTurnResult` | Interview/application compatibility facade | Move/remove this coordinator with interview functionality. It is not required by graph generation. |

No inbound import was found from:

- `bot0_thought_graph.thought_generation`; 
- `bot0_thought_graph.reflection`; 
- `bot0_thought_graph.providers`; 
- `bot0_thought_graph.models`; or
- `bot0_thought_graph.storage`.

This means there is currently no core-to-interview dependency. The
`orchestration` coordinator is the one exception to a strictly graph-only
package-wide import boundary, but it is an interview-specific optional surface,
not a dependency of the core generation path.

### Legacy source

`src/agents/state_transition_machine.py` imports
`bot0_thought_graph.interview.topic_exhaustion.TopicExhaustionPolicy` and aliases
it as `TopicExhaustionService`. This is a legacy/application dependency, not a
canonical graph-generation dependency. Before deleting `interview/`, either
move the policy to the future interview package and update that legacy caller,
or explicitly retire the legacy caller. The legacy tree is not otherwise being
cleaned in this audit.

### Tests

| Consumer | Imported capability | Classification | Extraction action |
|---|---|---|---|
| `tests/test_interview_orchestration.py` | Interview engine, models, answer evaluation, state, orchestration coordinator and interview policy | Interview-specific | Move/rewrite with the external interview package; preserve behavioral coverage there. |
| `tests/test_reflection_decomposition.py` | Decomposition through `bot0_thought_graph.interview.reflection` | Compatibility test | Migrate the primary evaluator tests to `bot0_thought_graph.reflection`; retain one explicit compatibility test only while the shim is supported, then remove it. |
| `tests/test_reflection_package_boundary.py` | Old decomposition import and root interview-free import | Package-boundary/compatibility test | Keep the interview-free boundary assertion; remove the old-import assertion when the shim and interview namespace are intentionally removed. |
| `tests/test_package_hygiene.py` | Root wildcard export includes `InterviewEngine` | Compatibility/public API test | Update when the root export is deprecated/removed; do not weaken graph package hygiene. |
| `tests/test_topic_exhaustion_service.py` | Topic exhaustion behavior | Interview-specific/legacy compatibility coverage | Move with interview policy or legacy application code, depending on its intended consumer. |
| `tests/test_interviewagent_support.py` | Legacy `src/interviewagent_support.py` | Legacy test | Not a canonical interview package test; leave outside this extraction or retire with the legacy application. |
| `tests/test_question_generator_async.py` | Legacy `agents.question_generator_async` | Legacy test | Leave outside canonical extraction; it does not test `bot0_thought_graph.interview`. |
| `tests/test_question_generator_async_integration.py` | Legacy async agent integration | Legacy test | Leave outside canonical extraction. It currently fails collection because `aiohttp` is unavailable. |

The two `aiohttp`-blocked tests are legacy async-agent tests, not tests of the
canonical synchronous interview subsystem. No dependency should be installed
for this audit.

### Examples and documentation

- `examples/interview.py` imports `InterviewEngine` from the root package. Move
  or replace it with an example owned by the future interview package.
- `examples/explicit_persistence.py` imports both `InterviewEngine` and
  `JsonRepository`. Split the interview example from the graph storage example,
  or move it with the external interview package.
- `docs/release_readiness_v0.1.0.md`, `docs/public_api.md`, and related
  architecture documents describe the interview capability. Update them when
  the removal/deprecation is implemented, not as part of this audit.

No script was found that imports the canonical `InterviewEngine` directly.

## 4. Outbound dependency map

The interview subsystem depends on stable package capabilities as follows:

| Interview component | Package dependency | Need in future external package |
|---|---|---|
| `interview/engine.py` | `bot0_thought_graph.models.IdeaJSONModel`, `IndexedIdeaJSONModel`; `providers.LLMProvider`; `storage.Repository`; `thought_generation.index_idea`; local interview services/models/policies | Import graph/domain models, provider protocol, repository contract, and graph indexing through public package APIs. |
| `interview/question_generation.py` | `models.EvaluationCriteria`; interview prompts; `providers.GenerationRequest`, `LLMProvider`, `ProviderResponseError` | Use provider request/protocol and the answer criteria contract; interview question prompts can move with the interview package. |
| `interview/reflection/answer_evaluation.py` | `models.EvaluationCriteria`, `EvaluationJSONModel`; interview answer prompt; `providers.GenerationRequest`, `LLMProvider`; `reflection.shared.generate_structured` | Use package-level structured provider plumbing or a future stable public helper; answer-evaluation semantics and prompt belong externally. |
| `interview/reflection/policy.py` | `models.EvaluationCriteria`; local `ReflectionDecision` | Keep policy and action model external; consume the answer-evaluation result contract. |
| `interview/models.py` | `models.EvaluationCriteria`, `IndexedIdeaJSONModel`; Pydantic | Keep interview session state external while referencing graph models from the core package. |
| `interview/state.py` | `models.IndexedIdeaJSONModel` | Consume the indexed graph contract from the core package. |
| `interview/topic_exhaustion.py` | Standard library only | Move unchanged to the external interview/application package. |
| `interview/reflection/decomposition.py` | `bot0_thought_graph.reflection.decomposition` | No external interview dependency is needed; callers should use the core reflection package directly. |
| `interview/reflection/shared.py` | `bot0_thought_graph.reflection.shared` | No separate shim is needed externally once answer evaluation moves. |

The future consuming package should receive a provider instance and model name,
and should depend on core graph contracts rather than importing internal engine
modules. The interview package may use `ThoughtGraphEngine` when it needs to
generate a graph, but graph generation must not import interview services.

## 5. Core-path and behavior protection findings

The core adaptive path is:

```text
ThoughtGraphEngine
  -> thought_generation
  -> bot0_thought_graph.reflection.decomposition
  -> providers/models/prompts/storage
```

`ThoughtGraphEngine` no longer imports `bot0_thought_graph.interview` or its
reflection namespace. Package-level `reflection` owns decomposition and shared
structured provider invocation. Removing interview therefore must not touch
the following:

- horizontal or vertical generation;
- decomposition prompt, contract, or focused/balanced/rich semantics;
- recursive traversal and candidate retention;
- novelty, endpoint, relevance, branch-pruning, or marginal-value guards;
- graph models;
- provider adapters or model selection;
- safety limits, provider-call accounting, or fallback behavior.

The interview components most likely to cause accidental behavior changes are
the decomposition compatibility shims and any broad `__init__.py` edits. The
shims must not be mistaken for the decomposition implementation. The engine’s
import must remain `bot0_thought_graph.reflection`; only interview-facing
imports should be removed.

## 6. Root `InterviewEngine` analysis

Phase A removed eager interview loading from the root package while preserving:

```python
from bot0_thought_graph import InterviewEngine
```

through a lazy `__getattr__` compatibility export.

Current consumers are:

- `examples/interview.py`;
- `examples/explicit_persistence.py`;
- `tests/test_package_hygiene.py`; and
- `tests/test_interview_orchestration.py` imports `InterviewEngine` from the
  interview subpackage directly, not the root, but validates the same service.

The root export is compatibility-only relative to the target architecture. If
removed immediately, the two examples and callers using the documented root
import break. The safest extraction sequence is to publish the external
interview package, update examples and documentation, issue a deprecation
notice for the root export if compatibility matters, and remove the lazy export
in a deliberate breaking/pre-1.0 API change. The root graph package should not
retain an interview import solely for this compatibility path indefinitely.

## 7. Reflection shim analysis

The three Phase A surfaces have these current consumers:

| Shim | Current consumers | Can disappear with `interview/`? |
|---|---|---|
| `interview/reflection/__init__.py` | `interview/engine.py`, `interview/__init__.py`, interview tests, and old callers of the mixed reflection namespace | Yes, after interview services move and old callers migrate. |
| `interview/reflection/decomposition.py` | The compatibility package itself and callers/tests importing the old decomposition path | Yes. No core code requires it; the implementation remains in `bot0_thought_graph.reflection`. |
| `interview/reflection/shared.py` | `interview/reflection/answer_evaluation.py` currently imports package-level shared plumbing directly; old direct callers may still use the shim | Yes, after answer evaluation moves and any direct old imports migrate. |

There is no blocker in core code. The only blockers are compatibility callers
and the temporary promise to preserve old imports. The decomposition batching,
structured validation, exact ID reconciliation, and terminal/decompose behavior
are already covered by package-level tests and do not depend on the shim.

## 8. Interview-specific test disposition

The tests divide into four groups:

### Core thought-graph tests

`test_adaptive_decomposition_integration.py`, `test_concept_first_api.py`,
`test_thought_generation_package.py`, and related package model/provider tests
exercise graph generation. They must remain in the core package and must not
be moved with interview code. Their decomposition imports should stay
package-level.

### Interview-specific tests

`test_interview_orchestration.py` and `test_topic_exhaustion_service.py`
should move to the external interview package, retaining coverage for session
lifecycle, answer evaluation, follow-up/advance policy, exhaustion, and
optional persistence coordination.

### Compatibility tests

The old decomposition import assertion in
`test_reflection_package_boundary.py` and the root-export assertion in
`test_package_hygiene.py` should remain only through the compatibility window.
The interview-free root-import assertion should remain as a permanent core
boundary test.

### Legacy tests

`test_question_generator_async.py`,
`test_question_generator_async_integration.py`, and
`test_interviewagent_support.py` cover legacy top-level application modules.
They are not migration blockers for the canonical package once direct canonical
imports are removed. The first two currently cannot be collected because
`aiohttp` is missing; this audit intentionally does not install it.

## 9. Exact blockers to deleting `bot0_thought_graph/interview/`

Before deletion, all of the following must be addressed:

1. Move or remove `bot0_thought_graph.orchestration.coordinator`, which imports
   interview models and `InterviewEngine`.
2. Remove, deprecate, or replace the root lazy `InterviewEngine` export.
3. Migrate `examples/interview.py` and the interview portion of
   `examples/explicit_persistence.py`.
4. Move/rewrite `tests/test_interview_orchestration.py` and
   `tests/test_topic_exhaustion_service.py` under the future interview package.
5. Migrate or retire `src/agents/state_transition_machine.py`’s import of
   `TopicExhaustionPolicy`, if the legacy application remains in supported use.
6. Migrate callers of the compatibility paths
   `bot0_thought_graph.interview.*`, including old decomposition reflection
   imports.
7. Update package/API/release documentation and any packaging or CI references
   that promise the in-package interview surface.

The two legacy async-agent tests are not blockers to deleting the canonical
interview tree, but their separate legacy dependency failure should remain
explicit in test reporting.

## 10. Proposed extraction/removal sequence

1. Define and publish the external interview package boundary around the
   existing synchronous interview engine, models, question generation, answer
   evaluation, policy, state, and exhaustion capabilities.
2. Make that package depend on stable `bot0_thought_graph` provider, graph-model,
   indexing, storage, and reflection helper contracts.
3. Move interview tests and examples, preserving their existing semantics.
4. Move or retire `InterviewCoordinator` and any interview-only orchestration
   policy.
5. Update legacy application consumers that still use canonical interview
   modules, or explicitly mark those consumers unsupported/deferred.
6. Deprecate and then remove the root `InterviewEngine` lazy export and update
   package hygiene/API tests.
7. Remove the three reflection compatibility shims and the remaining
   `interview/` tree.
8. Run core graph tests and a clean subprocess import check proving that the
   installed graph package contains no interview namespace dependency.

## 11. Deletion criteria

Deletion is safe when all of these are true:

- `rg` finds no supported source, test, example, script, or packaging reference
  to `bot0_thought_graph.interview` or `InterviewEngine`;
- `thought_generation`, `reflection`, `providers`, `models`, `storage`, and
  root graph imports pass in a clean environment without loading interview;
- the external interview package owns and passes the migrated interview tests;
- the root export has been intentionally removed or completed its deprecation
  window;
- orchestration coordinator ownership is external or removed;
- legacy consumers have an explicit migration/retirement decision;
- core adaptive tests confirm unchanged decomposition and traversal behavior;
- package metadata and documentation no longer promise `interview/` as a
  permanent package surface.

## 12. Unresolved questions

1. Which separately named package/application will own the extracted interview
   services and their release/deprecation policy?
2. Should the structured helper `reflection.shared.generate_structured` become
   a documented public API for the external interview package, or should answer
   evaluation retain a private equivalent outside the core package?
3. Is `bot0_thought_graph.orchestration` intended to remain as a graph-only
   namespace, or should the interview coordinator be removed altogether?
4. How long should the root `InterviewEngine` compatibility export remain,
   given the package is currently pre-1.0?
5. Are legacy async-agent modules still supported by the repository, or should
   their tests and dependency issues be handled in a separate legacy cleanup?

## Conclusion

There is no remaining core `bot0_thought_graph` → `interview` dependency in the
graph-generation/reflection path. The canonical interview subsystem is
application-specific and should be extracted, not migrated into another core
responsibility.

The Phase A reflection shims can disappear once their old callers migrate. The
root `InterviewEngine` export can also disappear, but should be deprecated or
updated alongside the external package and examples. The main package-internal
dependency requiring explicit handling is the interview-specific orchestration
coordinator; the main legacy dependency is the topic-exhaustion shim used by
`src/agents/state_transition_machine.py`.

No files were moved or deleted, no imports or tests were changed, and no
thought-generation behavior was modified for this audit.

## Phase C completion note

Phase C subsequently removed the canonical `bot0_thought_graph.interview/`
tree, the interview-only `bot0_thought_graph.orchestration/` namespace, the
root `InterviewEngine` export, and the interview-only examples and tests. The
legacy async application still owns its topic-exhaustion implementation in
`src/agents/state_transition_machine.py`; this avoided adding an interview
policy back to the graph package or beginning broad legacy cleanup.

The decomposition tests now use `bot0_thought_graph.reflection` directly, and
the package-boundary tests assert that the interview namespace is unavailable.
The remaining interview references in this document are historical audit
evidence or extraction guidance, not live package dependencies.
