# Adaptive Vertical Decomposition Evaluation Audit

Date: 2026-09-14

## Scope and conclusion

This audit examines whether the repository's existing agent/evaluator code can make the adaptive vertical decomposition decision:

> Would decomposing this retained thought one more level add enough meaningful
> value to justify another provider call?

Recommendation: **partial reuse, but not reuse of `EvaluatorAgentAsync` or `EvaluationService` as-is**. Both existing evaluators assess an answer to a question. Neither evaluates the expected value of decomposing a thought. The smallest clean implementation is a thought-generation-specific decomposition evaluator contract, using the package's existing provider/request/parsing mechanisms and retaining the current deterministic heuristics as prefilters and fallbacks.

This recommendation preserves the repository's dependency boundary: the core package must not import the legacy controller/agent layer. The documented boundary explicitly keeps `EvaluatorAgent` outside the core library and keeps reusable scoring mechanisms inside it (`docs/agent_policy_boundary.md:20-40`).

## 1. Existing evaluator architecture

### Legacy `EvaluatorAgentAsync`

`src/agents/evaluator_agent_async.py:63-267` defines `EvaluatorAgentAsync`. Its responsibility is evaluating a user's answer to a question. `evaluate_async()` accepts:

```text
question, answer, idea, thought
```

and formats `QUESTION_ANSWER_EVAL_PROMPT` (`:123-154`). The response is parsed as `EvaluationJSONModel`, whose criteria are the existing answer-evaluation dimensions; the agent also exposes a composite score and a correctness threshold (`:235-267`).

This is an asynchronous application-era agent. It imports and constructs provider clients directly (`:94-101`), routes between legacy OpenAI/Claude/Llama helpers (`:179-224`), and uses legacy `models`, `prompts`, and `utils` modules. It is not provider-neutral at the package contract level.

### Package `EvaluationService`

`src/bot0_thought_graph/interview/reflection/answer_evaluation.py` defines the reusable `EvaluationService` under the Reflection subsystem. It receives the package `LLMProvider`, constructs a provider-neutral `GenerationRequest`, and uses the shared Reflection structured-response helper to extract and validate the response. `interview/evaluation.py` remains only as a compatibility import.

Its responsibility is still answer evaluation. It accepts the same semantic inputs—`question`, `answer`, `idea`, and `thought`—and returns `EvaluationCriteria` (`:27-43`). Its scoring helpers average the existing criteria or test the correctness threshold (`:45-51`). It has no concept of an ancestor path, covered conceptual ground, decomposition, decomposition value, or exploration profile.

### Existing provider-neutral mechanisms

The package already provides the reusable lower-level pieces needed for a new decomposition evaluator:

- `LLMProvider.generate(GenerationRequest) -> GenerationResult`,
  `src/bot0_thought_graph/providers/contracts.py:34-52`;
- JSON extraction and response validation used by `EvaluationService`;
- package model and prompt boundaries;
- deterministic overlap/relevance utilities in `ThoughtGraphEngine`.

These mechanisms are suitable for reuse without importing the legacy agent package.

## 2. Reuse suitability

**Verdict: partial, with no direct evaluator-class reuse.**

The existing `EvaluationService` can be reused as an architectural pattern and possibly as a low-level provider-call/parser utility, but its current prompt, output schema, and criteria are incompatible with decomposition worthiness. Reusing it directly would distort its responsibility by treating answer quality—correctness, clarity, specificity, and relevance—as a proxy for the value of another thought-graph level.

`EvaluatorAgentAsync` is a stronger **no**. It would introduce legacy imports, async lifecycle requirements, provider construction, old model identifiers, and coupling from `bot0_thought_graph` into `src/agents`. That reverses the documented dependency direction (`docs/agent_policy_boundary.md:53-59`).

Reuse would therefore require a new evaluation criterion/mode and output contract, not merely passing a different value to the current evaluator. The clean change is small in behavior but is a new thought-generation evaluation mechanism, not a mode added to answer evaluation.

## 3. Proposed decomposition-evaluation contract

The contract should be provider-neutral and synchronous, matching the current
`ThoughtGraphEngine` traversal. Each request evaluates all eligible retained
children from one vertical generation result in a single batch:

```python
DecompositionCandidate:
    id: str
    thought: str
    description: str | None

DecompositionEvaluationRequest:
    ancestor_path: tuple[str, ...]  # [0] is root; [-1] is current parent
    candidates: tuple[DecompositionCandidate, ...]
    exploration: Literal["focused", "balanced", "rich"]

DecompositionDecision:
    candidate_id: str
    decompose: bool
    reason: str

DecompositionEvaluationResult:
    decisions: tuple[DecompositionDecision, ...]
```

The path is required to be non-empty. The root concept is derived from
`ancestor_path[0]`, and the current parent is derived from
`ancestor_path[-1]`; neither is repeated as a separate field. Candidate
descriptions remain because they provide semantic information not guaranteed by
the thought name alone. `progression_type` belongs to vertical child
generation, not to the decomposition-worthiness decision. `covered_context` is
not included initially because current sibling/path novelty checks already
provide the available cross-branch guard without adding graph state.

The result is a decision contract, not a quality score:

```text
candidate_id          = stable local ID from the request
decompose  = whether another vertical decomposition is worthwhile
reason                = stable diagnostic category
```

`value: float` is intentionally omitted from the minimum result. A boolean
decision and stable reason are sufficient for traversal; a numeric diagnostic
can be added later only if calibration demonstrates a need.

## 4. Proposed call flow and placement

The current adaptive path is:

```text
_generate_adaptive_graph()
  -> _generate_adaptive_horizontal()
  -> for each root child:
       _expand_adaptive_node()
         -> provider vertical generation
         -> novelty filtering / retention
         -> branch pruning
         -> root-goal relevance
         -> marginal-value heuristic
         -> recursive _expand_adaptive_node()
```

Evidence: root children are expanded in order at `src/bot0_thought_graph/thought_generation/engine.py:882-909`; vertical generation and retention occur at `:1011-1079`; branch pruning, relevance, and the current marginal-value gate occur at `:1086-1138`.

The evaluator belongs at the decomposition boundary, after a thought is retained and after cheap deterministic checks, but before the recursive call:

```text
retain child
  -> natural endpoint check
  -> lexical branch-pruning prefilter
  -> deterministic root-relevance prefilter
  -> decomposition evaluation
  -> decompose: recursive expansion
     stop: retain terminal child and trace reason
```

An alternative cost-saving placement is to evaluate a retained parent before requesting its next vertical batch. That can avoid a generation call entirely, but it does not exactly implement the requested “for each retained thought” boundary and has less information about the candidate next level. The first implementation should choose one clear contract and test its accounting.

## 5. Existing heuristics: prefilters versus authority

Current deterministic logic should remain useful even if an evaluator is introduced:

- `_is_meaningful_candidate()` (`engine.py:1450` area) remains the novelty and
  duplicate filter;
- `_is_relevant_candidate()` (`engine.py:1325` area) remains a cheap root-goal
  relevance guard and fallback when evaluation is unavailable;
- `_is_marginally_valuable_candidate()` (`engine.py:1262-1323`) can remain a
  conservative prefilter, especially for obvious repeated procedural detail;
- natural endpoint detection, branch pruning, depth guard, and safety budgets
  remain independent protections.

The LLM evaluator should become authoritative only for the narrower semantic question that the heuristics cannot answer reliably: whether another level is worth exploring. It should not replace novelty, root relevance, candidate retention, or graph safety guards. A failed/invalid evaluator response should fall back to the deterministic policy and produce a diagnostic reason rather than silently dropping the branch.

The current marginal heuristic is provider-neutral but lexical/structural. It subtracts root and established-path vocabulary, discounts detail/procedural terms, and penalizes repeated procedural levels. This is a reasonable cheap prefilter, but it cannot reliably recognize semantic novelty expressed with unrelated vocabulary. That limitation is the strongest case for a semantic decomposition evaluator.

## 6. Provider/model neutrality and coupling risk

`EvaluationService` is provider-injected and therefore neutral at the package contract level. `EvaluatorAgentAsync` is not: it selects legacy providers and constructs their clients itself. The thought-generation engine should not import either legacy agent or legacy model/prompt modules.

A new decomposition evaluator can remain neutral if it accepts the existing `LLMProvider`, model, temperature, token, and timeout values in the same manner as the package generation services. The prompt should be owned by the thought-generation package because decomposition is graph-construction policy, not interview answer evaluation.

The main coupling risk is conceptual rather than technical: sharing the `EvaluationCriteria` schema would make graph decomposition depend on answer quality dimensions. A dedicated small result schema avoids that coupling.

## 7. Provider-call and token impact

Current adaptive vertical expansion makes one provider call per recursively expanded node, with up to four requested children. A separate evaluator call for each retained child could multiply calls substantially and could consume the existing adaptive call/expansion budgets before useful generation occurs.

Preferred accounting options, in order:

1. Batch decomposition decisions for all retained children of one vertical
   result in one evaluator call.
2. Evaluate the parent once before requesting its next vertical batch when the
   evaluator can judge decomposition from the accumulated path alone.
3. Avoid one evaluator call per child unless measurements show that its
   precision benefit justifies the cost.

The first option best matches the requested retained-child semantics. It adds approximately one evaluation call per vertical generation call, rather than one per child, and requires a compact structured response. The implementation must explicitly account for these calls under the existing safety budgets; it must not silently double-count or bypass them.

## 8. Profile behavior without fixed dimensions

Profiles should be passed as evaluation context or select internal acceptance thresholds/rubric wording:

```text
focused   -> reject borderline decomposition value
balanced  -> accept clearly meaningful value
rich      -> accept subtler but still defensible value
```

All profiles should evaluate the same evidence and share the same hard safety guards. No profile should select a fixed depth, child count, batch size, or graph-size target. Tests should compare overall calls, retained nodes, depth, and semantic stop reasons on identical deterministic provider evidence.

## 9. Smallest implementation plan

No implementation is made by this audit. If approved, the smallest next phase would be:

1. Add a thought-generation-specific decomposition request/result schema and a
   package-owned prompt or evaluator service; do not import `src/agents`.
2. Add a fake-provider response fixture and validate structured decomposition
   results, including malformed-response fallback.
3. Invoke the evaluator at the existing pre-recursion boundary, retaining
   children that fail decomposition evaluation.
4. Batch decisions per vertical result if the provider response contract
   supports it.
5. Keep novelty, root relevance, branch pruning, endpoint detection, depth,
   and safety guards unchanged.
6. Add trace reasons distinguishing evaluator decomposition stops, fallback,
   and existing heuristic stops.
7. Measure provider calls, generated/retained/expanded children, nodes, depth,
   and safety-stop incidence before deciding whether the evaluator's semantic
   benefit justifies its call cost.

## 10. Likely files to change in a future implementation

Likely implementation files:

- `src/bot0_thought_graph/thought_generation/engine.py` — decomposition boundary
  integration and trace accounting;
- a new package-owned module such as
  `src/bot0_thought_graph/thought_generation/decomposition.py` — request/result
  contract and provider-backed evaluation mechanism;
- `src/bot0_thought_graph/prompts/thought_generation_prompt_templates.py` —
  only if a dedicated decomposition prompt is required;
- `src/bot0_thought_graph/thought_generation/__init__.py` — only if the new
  internal mechanism needs package-local export;
- `tests/test_concept_first_api.py` and/or a focused decomposition test module —
  deterministic policy, batching, fallback, trace, and budget accounting.

Files that should not change for this purpose:

- `src/agents/evaluator_agent_async.py`;
- provider adapters;
- graph models;
- public `generate_thought_graph()` controls;
- horizontal exploration and adaptive batch-size constants.

## Final recommendation

Do not reuse the existing evaluator classes directly. Reuse the package's provider-injected request, parsing, validation, and scoring patterns. Add a small dedicated decomposition-value mechanism only if deterministic heuristics remain inadequate after measuring semantic drift. Keep the current heuristics as cheap prefilters and fallback guards, and batch any new provider evaluation to prevent decomposition quality from recreating the token/call waste that the adaptive traversal was designed to reduce.
