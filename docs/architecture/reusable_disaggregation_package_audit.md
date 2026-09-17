# Reusable Complex-Topic Disaggregation Package Audit

> **Status: superseded for the end state.**
>
> This audit is retained as current-state evidence only. For the target architecture, see `interview_package_extraction_requirements.md` (authoritative) and `reusable_thought_graph_target_architecture.md` (summary). Where this audit's end-state recommendations conflict with those documents — specifically the retention of `bot0_thought_graph/interview/reflection/{answer_evaluation,policy}.py`, the preservation of the `InterviewEngine` root export, and the treatment of root `generate_thought_graph` as optional — the requirements document wins.

Date: 2026-09-16

## Executive conclusion

`bot0-thought-graph` is installable as a package and its canonical `ThoughtGraphEngine` API can generate a structured thought graph without a caller importing legacy agents, pipelines, or top-level compatibility modules. However, the package does not yet satisfy the stricter architectural goal of providing disaggregation independently of interview-specific architecture:

1. `from bot0_thought_graph import generate_thought_graph` is not currently a supported import. The public entry point is `ThoughtGraphEngine.generate_thought_graph()`.
2. `bot0_thought_graph/__init__.py` eagerly imports `InterviewEngine`, so a root package import loads the interview package even for graph-only use.
3. Adaptive graph traversal imports decomposition evaluation from `bot0_thought_graph.interview.reflection` at runtime.

The current behavior is usable, but the ownership boundary is not clean. The smallest supported cleanup is to give decomposition and its structured reflection plumbing a package-level home, preserve interview compatibility imports, and decouple the root graph API from eager interview imports.

No implementation or file moves were made by this audit.

## 1. Current canonical package architecture

The installable package is `src/bot0_thought_graph/`. Its package configuration uses:

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["bot0_thought_graph*"]
```

Therefore the canonical installed surfaces are:

```text
bot0_thought_graph/
    models/             # Pydantic graph/domain models
    prompts/            # package-owned generation/evaluation prompts
    providers/          # provider protocol, requests, adapters, factory
    storage/            # optional repository contracts/implementations
    thought_generation/  # public engine, generation, expansion, parsing
    interview/           # optional interview engine and interview reflection
    orchestration/       # thin compatibility namespace
```

`ThoughtGraphEngine` is the canonical graph-generation façade. The package root exports it, along with graph models, `ProgressionType`, provider protocols, and storage implementations (`src/bot0_thought_graph/__init__.py:3-20`).

## 2. Current public disaggregation call path

The documented/current external workflow is:

```python
from bot0_thought_graph import ThoughtGraphEngine

engine = ThoughtGraphEngine(provider="openai", model="your-model")
graph = engine.generate_thought_graph(
    topic="hospital emergency department operations",
    exploration="balanced",
)
```

The requested function-style example is not currently implemented: `bot0_thought_graph` has `ThoughtGraphEngine`, but no root-level `generate_thought_graph` symbol. This is an API ergonomics gap, not a graph algorithm gap.

For adaptive generation, the current call flow is:

```text
ThoughtGraphEngine.generate_thought_graph()
  -> _generate_adaptive_graph()
  -> _generate_adaptive_horizontal()
  -> generate_array_of_thoughts()
  -> generate_horizontal()
  -> LLMProvider.generate(GenerationRequest)
  -> parse_idea()/validate_idea()
  -> _expand_adaptive_node() for each retained root child
  -> expand_vertical()
  -> LLMProvider.generate(GenerationRequest)
  -> parse_thought()/validate_idea()
  -> deterministic endpoint/novelty/branch/relevance/marginal guards
  -> bot0_thought_graph.interview.reflection.DecompositionEvaluationService
  -> recursive _expand_adaptive_node() when decompose=True
```

The decomposition import is specifically visible at `thought_generation/engine.py:1197-1201`. The engine owns traversal, budgets, graph mutation, and deterministic guards; the evaluator owns the semantic decomposition decision and structured provider response.

## 3. Runtime dependency path

### Graph-only explicit generation

The core explicit graph path requires:

```text
ThoughtGraphEngine
  -> models
  -> prompts
  -> providers (protocol/contracts; named adapters are lazy)
  -> storage.Repository type boundary
  -> thought_generation.generation/expansion/indexing/ranking/validation
```

The installed dependency set includes `pydantic`, `openai`, `anthropic`, `pandas`, and `tenacity` (`pyproject.toml:7-12`). `models/__init__.py` imports `llm_response_models.py`, which imports pandas, even though the basic graph path does not need tabular response functionality. Provider SDK adapters are lazy in `providers/__init__.py`; constructing a named provider loads the relevant adapter and SDK.

### Graph-only adaptive generation

Adaptive generation adds:

```text
thought_generation.engine
  -> interview.reflection.decomposition
  -> reflection.shared
  -> thought_generation.parsing
```

This is a real runtime dependency from core graph traversal into the interview package namespace. It is currently delayed until an eligible adaptive batch is about to be evaluated, but delaying the import does not remove the ownership coupling.

### Root package import

`bot0_thought_graph/__init__.py:3` imports `InterviewEngine` before importing `ThoughtGraphEngine`. Consequently, a simple `import bot0_thought_graph` loads `bot0_thought_graph.interview` and its question generation, answer evaluation, reflection policy, state, and exhaustion modules. A repository check confirms that legacy `agents` modules are not loaded by this import, but the package interview subsystem is loaded.

## 4. Reflection ownership classification

| Current component | Actual responsibility | Ownership | Finding |
|---|---|---|---|
| `interview/reflection/decomposition.py` | Decides whether a retained thought merits one more vertical decomposition; owns request/result models, prompt, batch call, and ID reconciliation | Core thought-generation reflection | It is not interview-specific and is currently in the wrong namespace for dependency ownership |
| `interview/reflection/shared.py` | Provider invocation, JSON extraction, typed validation, normalized malformed-response errors | Shared reflection/provider infrastructure | Genuinely reusable by decomposition and answer evaluation; package-level reflection is a better home |
| `interview/reflection/answer_evaluation.py` | Evaluates a user answer against question/idea/thought quality criteria | Interview-specific | Correctly belongs with interview capabilities |
| `interview/reflection/policy.py` | Converts answer evaluation into advance/follow-up/complete interview actions | Interview-specific | Correctly belongs with interview policy |

The directory grouping is currently broader than the responsibilities. The name “reflection” is not the problem; the problem is that graph-core decomposition is nested under `interview` and graph-core code imports it from there.

## 5. Is `interview/reflection` the wrong home?

Yes, for decomposition specifically. Decomposition reflection is invoked while constructing a thought graph, does not inspect user answers, and does not make interview decisions. Its request contract contains an ancestor path, retained thought candidates, and an exploration profile—not interview state or answer criteria.

`shared.py` is also broader than interview, although its current contents are small and reusable. `answer_evaluation.py` and `policy.py` should remain under `interview` after the migration.

## 6. Recommended target structure

The evidence supports this minimal target:

```text
src/bot0_thought_graph/
    reflection/
        __init__.py
        shared.py
        decomposition.py
    thought_generation/
        engine.py
        ...
    interview/
        reflection/
            __init__.py
            answer_evaluation.py
            policy.py
        ...
    models/
    providers/
    storage/
    public API in __init__.py
```

The package-level `reflection` namespace should expose decomposition models and the evaluator. Interview reflection should expose answer evaluation and policy and may retain compatibility re-exports for any existing callers. The engine should import decomposition from package-level reflection, not from interview.

This recommendation does not change decomposition semantics, profiles, prompts, traversal, graph models, provider adapters, or budgets.

## 7. Top-level legacy and parallel surfaces

| Surface | Status | Evidence and implication |
|---|---|---|
| `src/agents/` | Legacy/application layer | Imports old top-level `models`, `prompts`, utilities, SDK clients, and async agent code. It is used by legacy scripts/tests, not by the installed package. It is excluded by the setuptools package filter. |
| `src/models/` | Legacy compatibility/shim layer | Several modules re-export `bot0_thought_graph.models`; `user_state_models.py` is legacy-only. It supports legacy agents and is not part of the installed package. |
| `src/prompts/` | Legacy compatibility/shim layer | Re-exports package prompts for old agents/tests. It is not imported by canonical package thought generation. |
| `src/pipelines/` | Legacy/application orchestration | File-backed and terminal/application workflows. Some wrappers delegate to package thought-generation functions, but package consumers do not need them. They are excluded from the installed package. |
| `src/thought_generation/` | Stale/parallel legacy residue | No current source modules were found there; only compiled-cache residue was present. Canonical source is `src/bot0_thought_graph/thought_generation/`. |

The package also contains `bot0_thought_graph/orchestration/`, but its `coordinator.py` imports interview types and it is not on the canonical graph generation path. It should remain optional/compatibility-oriented unless a future audit establishes a separate need.

## 8. Package exports and installability

Current exports are coherent for the engine-oriented API:

- `bot0_thought_graph.__init__` exports `ThoughtGraphEngine` and graph models.
- `bot0_thought_graph.thought_generation.__init__` exports the engine, typed generation requests, parsing/validation helpers, and readers.
- `bot0_thought_graph.interview.__init__` exports interview services and models.
- `bot0_thought_graph.interview.reflection.__init__` exports both decomposition and interview reflection services, which reflects the current but mixed ownership.

An external project can install the wheel and call `ThoughtGraphEngine` without installing or importing `src/agents`, `src/models`, `src/prompts`, or `src/pipelines`. It does not need to know about interview internals at the call site. Nevertheless, the root package import and adaptive runtime path currently create an internal interview dependency.

## 9. Compatibility implications

Moving decomposition is low-risk if done as a compatibility-preserving move:

- Existing package callers importing `bot0_thought_graph.interview.reflection.DecompositionEvaluationService` may continue to work through a re-export shim.
- Existing answer-evaluation and policy imports remain unchanged.
- `ThoughtGraphEngine` behavior and provider-call accounting remain unchanged; only the import owner changes.
- The legacy `src/agents` tree is not a reason to retain the decomposition module under `interview`; it has no canonical package dependency.
- Removing eager `InterviewEngine` import from the package root could affect callers who rely on `from bot0_thought_graph import InterviewEngine`. Preserve that compatibility with a lazy export or an explicit compatibility path.

Adding a root-level function wrapper would be an API addition, not required for the ownership migration. It would make the desired function-style experience available while retaining `ThoughtGraphEngine` as the implementation façade.

## 10. Smallest migration plan

1. Add `bot0_thought_graph/reflection/` and move or copy the reusable `shared.py` and `decomposition.py` implementation there.
2. Change the adaptive engine import to the package-level reflection namespace.
3. Keep `interview/reflection/decomposition.py` as a compatibility re-export temporarily, or remove it only in a deliberate breaking-release cleanup.
4. Update `answer_evaluation.py` to consume package-level shared plumbing while keeping answer evaluation and `policy.py` under `interview`.
5. Make the root `InterviewEngine` export lazy or otherwise prevent interview imports from being required for graph-only package import.
6. Optionally add a thin root-level `generate_thought_graph` convenience function after deciding its provider/model defaults; this is an API design step, not necessary to relocate ownership.
7. Add import-boundary tests proving graph-only imports do not load interview modules, and compatibility tests for the old decomposition import path.

No profile, prompt, traversal, graph, provider, budget, or public engine behavior should change during this migration.

## 11. Likely files affected by a subsequent migration

Likely implementation changes:

- new `src/bot0_thought_graph/reflection/__init__.py`;
- new/moved `src/bot0_thought_graph/reflection/shared.py`;
- new/moved `src/bot0_thought_graph/reflection/decomposition.py`;
- `src/bot0_thought_graph/thought_generation/engine.py` import site;
- `src/bot0_thought_graph/interview/reflection/__init__.py` compatibility exports;
- `src/bot0_thought_graph/interview/reflection/answer_evaluation.py` shared helper import;
- `src/bot0_thought_graph/__init__.py` import boundary and possibly a function façade;
- focused import/compatibility tests.

Files that should not be changed for this ownership migration:

- provider adapters;
- graph models;
- adaptive thresholds and budgets;
- horizontal/vertical generation semantics;
- `src/agents/`, `src/models/`, `src/prompts/`, and `src/pipelines/` legacy implementations.

## Final answer to the package-boundary question

**Partially, but not cleanly enough for the stated architecture.** Another Python project can install `bot0-thought-graph` and use `ThoughtGraphEngine.generate_thought_graph()` without directly depending on interview agents or legacy top-level packages. It cannot use the exact stated function-style import today, and adaptive graph generation internally depends on `interview/reflection` while the package root eagerly loads interview code.

The smallest architecture cleanup is therefore to separate package-level decomposition reflection from interview answer evaluation/policy and make the root graph import independent of interview loading, while preserving compatibility re-exports during migration.

## Phase A implementation status

Phase A was implemented after this audit's initial snapshot. The core reflection
implementation now lives under `bot0_thought_graph/reflection/`:

- `reflection/decomposition.py` owns the decomposition models, prompt, evaluator,
  structured validation, and exact candidate-ID reconciliation.
- `reflection/shared.py` owns provider invocation and structured-response
  plumbing.
- `interview/reflection/decomposition.py` and `interview/reflection/shared.py`
  are compatibility re-export shims.
- Interview answer evaluation and policy remain under
  `interview/reflection/`.
- `ThoughtGraphEngine` imports decomposition reflection from the package-level
  namespace, and the root `InterviewEngine` export is lazy. A graph-only root
  import therefore does not eagerly load `bot0_thought_graph.interview`.

The migration changed ownership and imports only. Decomposition contracts,
prompts, profiles, traversal, guards, graph behavior, provider adapters, and
budget semantics were not changed. The exact function-style
`generate_thought_graph` convenience API remains outside this Phase A scope.
