# Thought-generation breadth/depth audit

Audit scope: repository state on 2026-09-10. This is an implementation audit; it does not change production code or tests.

## Executive findings

- **VERIFIED:** The canonical package is `src/bot0_thought_graph/thought_generation`. Its graph façade performs one horizontal request for the root's first-level children, then recursively performs vertical requests for descendants (`engine.py:486-583`, `_expand_graph_node` at `engine.py:586-636`).
- **VERIFIED:** Horizontal generation is batch generation of sibling-level dimensions. Its requested count is `num_thoughts`/`max_subtopics`; the prompt asks for an exact count, but parsing does not enforce that count (`generation.py:10-35`, `prompts/thought_generation_prompt_templates.py:253-268`).
- **VERIFIED:** Vertical generation is a one-call batch of direct children of one selected thought. Graph traversal is a bounded tree, not a single linear continuation (`expansion.py:10-75`, `engine.py:586-636`).
- **VERIFIED:** `progression_type` belongs to vertical expansion only. It is an enum normalized at vertical request/function boundaries and interpolated into the vertical prompt; horizontal request generation has no such field (`models/thought_models.py:12-18`, `engine.py:29-105`, `expansion.py:10-35`).
- **INFERRED:** The asymmetry hypothesis is supported by the architecture: horizontal breadth is a sibling batch at the root, while depth multiplies vertical expansions over nodes. However, the current defaults are not asymmetric in the proposed sense: graph defaults are `breadth=6`, `depth=2`, and the façade hard-caps depth at 3 (`engine.py:138`, `engine.py:486-557`).

## Canonical runtime call paths

### Typed horizontal request

```text
ThoughtGraphEngine.generate(HorizontalGenerationRequest)
  -> generation.generate_horizontal()
  -> THOUGHT_GENERATION_PROMPT or request.prompt_template
       .format(idea, num_sub_thoughts=num_thoughts)
  -> provider.generate(GenerationRequest)
  -> validation.parse_idea()
  -> IdeaJSONModel
  -> optional ranking.select_clusters()
       -> provider.generate() -> IdeaClusterJSONModel
       -> ranking.convert_clusters_to_idea()
```

Sources: `thought_generation/engine.py:175-223`, `generation.py:10-35`, `ranking.py:31-76`, `validation.py:29-39`.

### Typed vertical request

```text
ThoughtGraphEngine.expand(VerticalGenerationRequest)
  -> expansion.expand_vertical()
  -> ProgressionType(progression_type)
  -> VERTICAL_SUB_THOUGHT_GENERATION_PROMPT or request.prompt_template
       .format(idea, thought, progression_type.value, num_sub_thoughts)
  -> provider.generate(GenerationRequest)
  -> validation.parse_thought()
  -> ThoughtJSONModel with sub_thoughts
```

Sources: `engine.py:228-263`, `expansion.py:10-42`, `prompts/thought_generation_prompt_templates.py:190-237`.

### Concept-first graph façade

```text
ThoughtGraphEngine.generate_thought_graph(
    concept/topic, depth, breadth, progression_type
)
  -> generate_array_of_thoughts(concept, max_subtopics=breadth)
       -> HorizontalGenerationRequest(num_thoughts=breadth)
       -> generate_horizontal -> provider -> parse_idea
  -> root = ThoughtNode(concept, first breadth horizontal children)
  -> for each first-level child, if depth >= 2:
       _expand_graph_node(child, level=1)
         -> _expand_subtopic_result(... max_details=breadth,
                                    progression_type=selected enum)
         -> VerticalGenerationRequest
         -> expand_vertical -> provider -> parse_thought
         -> replace node.children with returned children[:breadth]
         -> recurse for each child until level >= depth
  -> ThoughtGraph(concept, root, depth, breadth)
```

Sources: `engine.py:427-483`, `engine.py:486-636`, `models/thought_models.py:30-48`.

The graph mutates `ThoughtNode.children` in place. There are no explicit edge objects or edge labels; every relationship is represented as a generic parent node with child nodes. `ThoughtGraph.depth` and `.breadth` are requested metadata, not measured statistics (`models/thought_models.py:42-48`).

## Ownership map

- **Public façade:** `ThoughtGraphEngine`; see `thought_generation/engine.py` and package exports in `__init__.py`.
- **Typed generation configuration:** `HorizontalGenerationRequest` and `VerticalGenerationRequest`; see `engine.py:29-105`.
- **Horizontal generation:** `generation.generate_horizontal`; see `generation.py:10-35`.
- **Vertical expansion:** `expansion.expand_vertical` and `expand_idea`; see `expansion.py:10-75`.
- **Progression type:** `models.ProgressionType` plus vertical request/function boundaries; see `models/thought_models.py:12-18` and `engine.py:103-105`.
- **Prompting:** `prompts/thought_generation_prompt_templates.py`; its constants are imported by generation, expansion, and the engine.
- **Provider invocation:** `LLMProvider.generate` implementations; see `providers/contracts.py:8-66`. Adapters are lazy-loaded by `providers/__init__.py`.
- **Graph expansion:** `ThoughtGraphEngine._expand_graph_node`; see `engine.py:586-636`.
- **Stopping:** `depth`/`MAX_FACADE_DEPTH`, the recursion guard, and returned list exhaustion; see `engine.py:138` and `engine.py:553-614`.
- **Generation limits:** request counts, façade `breadth`, `MAX_FACADE_DEPTH`, and provider `max_tokens`; see `engine.py`, `generation.py`, `expansion.py`, and `providers/contracts.py`.
- **Validation:** façade `_require_text`/`_require_positive`, enum conversion, Pydantic models, and JSON parsing; see `engine.py:647-700`, `validation.py`, and `models/thought_models.py`.
- **Result construction:** `ThoughtArray`, `ThoughtGraph`, `ThoughtNode`, and legacy JSON models; see `engine.py:427-583` and `models/thought_models.py`.

## Current semantics

### Horizontal

**VERIFIED:** A horizontal thought is a sibling-level major dimension of an idea, intended to have similar abstraction, broad coverage, and minimal overlap. The concept prompt explicitly excludes implementation steps, actions, examples, and details belonging under a subtopic (`prompts/...prompt_templates.py:253-268`).

In the graph façade, horizontal generation occurs only for the root: the returned `ThoughtArray` becomes `root.children`. The recursive graph path never calls horizontal generation for arbitrary nodes. Lower-level `generate_horizontal()` can of course be called for any supplied `idea`, and `expand_all()` is a separate operation over all existing top-level thoughts (`expansion.py:44-75`).

`breadth` currently means the maximum number of retained children at every expanded graph node. Because the same value is used for the root horizontal request and each vertical child request, it is not an independent horizontal and vertical control (`engine.py:561-583`, `engine.py:619-626`).

### Vertical

**VERIFIED:** A vertical thought is a more-specific direct child below one parent thought. A vertical expansion requests `num_sub_thoughts` children in one response; it does not request one next thought at a time (`expansion.py:10-42`).

In the graph, `depth=1` means root plus the first horizontal child level; `depth=2` adds one vertical expansion under each first-level child; `depth=3` adds another child level. Thus current `depth` means maximum generated child levels beneath the root, not exactly N generated thoughts and not a count of provider steps (`engine.py:504-516`).

Vertical expansion can branch: every returned child is recursively expanded when another level remains. It is therefore a rooted tree of repeated parent-to-direct-children decompositions, not fundamentally a linear chain. Provider order is preserved, but semantic sequence and edge direction are not stored as graph metadata (`models/thought_models.py:22-35`; tests below).

### `progression_type`

**VERIFIED:** It controls the intended semantic relationship and wording of vertical children: `implementation_steps`, `simple_to_complex`, `chronological`, `problem_solution`, or `prerequisite_dependency`. It is accepted by `VerticalGenerationRequest`, `expand`, `expand_all`, `expand_subtopic`, and `generate_thought_graph`, and reaches vertical prompts. It is absent from `HorizontalGenerationRequest` and `generate_horizontal`.

**VERIFIED:** It does not control breadth, depth, traversal, stopping, graph branching, or provider behavior. It is not stored in `ThoughtJSONModel`, `ThoughtNode`, or `ThoughtGraph`. The output is only structurally validated; the package does not verify that a child is actually chronological, causal, or a strict prerequisite (`validation.py:35-39`, `models/thought_models.py:20-48`).

## Limits and stopping behavior

- Typed horizontal requests default to `num_thoughts=10`; typed vertical requests default to `num_sub_thoughts=7`; `expand_all` defaults to 5. These values are prompt request sizes, not guaranteed result sizes (`engine.py:57`, `engine.py:95`, `engine.py:271-272`).
- Concept-first array methods default to `max_subtopics=8`; detail methods to `max_details=8`; graph methods to `depth=2`, `breadth=6` (`engine.py:334`, `engine.py:378`, `engine.py:427`, `engine.py:491-492`).
- `MAX_FACADE_DEPTH=3` is the only explicit graph depth hard limit. Depth and breadth must be positive integers; invalid values raise `ValueError` (`engine.py:138`, `engine.py:553-557`, `engine.py:702-725`).
- Horizontal stopping is not an LLM decision. One provider call is made; the prompt asks for exactly N; the result is accepted and façade output is sliced to the requested maximum. Ranking, when enabled, adds one provider call and returns provider-selected clusters (`engine.py:197-223`, `engine.py:470-483`).
- Vertical stopping is not an LLM decision. The graph stops at the requested depth or when a provider returns no children. Each eligible node gets one call, so a full breadth-b tree can cause exponential call growth. There is no token, call, wall-clock, or total-node budget in graph orchestration beyond per-request `max_tokens` and provider timeout (`engine.py:598-626`, `providers/contracts.py:8-20`).
- Prompts ask for exactly the requested number (`THOUGHT_GENERATION_PROMPT`, `CONCEPT_SUBTOPIC_GENERATION_PROMPT`, and `CONCEPT_DETAIL_GENERATION_PROMPT`), but Pydantic parsing validates shape rather than cardinality.

## LLM decision-making today

**VERIFIED:** The LLM implicitly chooses the content and ordering of returned thoughts and may return fewer items despite an exact-count prompt. It does not currently choose whether to create another horizontal direction, whether to continue vertically, or the graph depth. Those decisions are made by caller arguments, fixed defaults, and Python recursion. The existing clustering path selects representative clusters, but it is not an open-ended breadth policy.

## Tests and contractual status

Relevant tests:

- `tests/test_concept_first_api.py:39-65` verifies façade translation, prompt selection, and provider settings.
- `tests/test_concept_first_api.py:108-138` verifies graph shape, depth/breadth metadata, one horizontal call plus one vertical call per first-level branch, and recursive child retention.
- `tests/test_concept_first_api.py:140-168` verifies `depth=1` has no vertical calls, breadth slicing, and progression propagation into vertical prompts.
- `tests/test_concept_first_api.py:170-181` verifies positive integer validation and the depth-3 hard cap.
- `tests/test_thought_generation_package.py:38-104` verifies provider injection, order preservation, progression normalization, and deterministic `expand_all` input order.
- `tests/test_package_models_and_prompts.py:82-84` verifies prompt formatting.

**CONTRACTUAL (tested/documented):** accepted public signatures, positive integer validation, `depth=1/2` graph shape, breadth truncation, provider call count for the tested shape, source order, enum values/normalization, and progression text in vertical prompts.

**CURRENT IMPLEMENTATION BEHAVIOR (not a strong semantic contract):** the LLM returns exactly the requested cardinality, generated names are materially distinct, a progression is truly linear or prerequisite-valid, and all graph branches have identical shape. No tests establish those properties.

## Legacy/canonical duplication

**VERIFIED:** There is no second installed thought-generation package layout. Packaging includes `bot0_thought_graph*` under `src` (`pyproject.toml`), and its exports point to the canonical engine (`src/bot0_thought_graph/__init__.py` and `thought_generation/__init__.py`).

`src/pipelines/horizontal_thoughts_pipeline.py` and `src/pipelines/vertical_thoughts_pipeline.py` are legacy-style file-persistence wrappers, but they import `bot0_thought_graph.thought_generation.ThoughtGraphEngine` and therefore reuse the canonical implementation. They retain older names, provider/model constants, clustering ratios, and JSON file I/O; they are not alternate breadth/depth algorithms. `src/run_thought_generation_pipeline.py` and `src/main_walid.py` call those wrappers. This is a duplicated orchestration surface, not duplicated core generation logic.

## Architectural gaps

1. There is no concept-first API with independent `horizontal` and `vertical` controls. Current graph `breadth` is shared by root horizontal children and every vertical child batch; current `depth` is only a fixed graph-level limit.
2. Horizontal generation is one-shot and root-only in graph construction; no material-distinctness decision or arbitrary-node horizontal expansion exists.
3. Vertical generation requests a sibling batch at each node, not an iterative continuation. There is no natural signal for “another step adds insufficient value” in the returned schema.
4. There are no hard total-call, total-node, token, or cost budgets for graph traversal. Provider timeout is per request, not an orchestration budget.
5. `ThoughtNode` has generic children only, so progression semantics are prompt intent rather than typed graph relationships.
6. The existing typed `generate(request)` returns `IdeaJSONModel`, while the concept-first graph method is named `generate_thought_graph`; blindly overloading `generate` with a concept string would create a result and compatibility ambiguity.
