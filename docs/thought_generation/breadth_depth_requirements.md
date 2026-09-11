# Breadth and Depth Requirements

These are proposed product and API requirements based on the implementation audit. They are not implemented by this change.

## Design Principles

The public API should separate two usage modes:

1. **Adaptive exploration** for normal callers. The caller supplies a concept and, optionally, an exploration profile. The engine decides how broadly and deeply to develop the thought graph.
2. **Explicit bounds** for advanced callers, deterministic tests, benchmarks, and workflows that require caller-controlled graph shape.

Ordinary callers should not need to understand graph depth, breadth, stopping thresholds, frontier traversal, provider-call budgets, or other orchestration details.

The underlying thought-generation primitives should remain responsible for generating requested thoughts. Adaptive exploration belongs primarily to orchestration: deciding what to expand, whether to continue, and when to stop.

## Core Semantics

### Horizontal

**Horizontal** describes materially distinct peer directions.

A useful horizontal thought adds meaningful coverage at approximately the same abstraction level. It should not merely be a synonym, implementation detail, example, or narrower restatement of an existing direction.

For explicit control:

```python
horizontal=2
```

means:

> Explore at most two root-level peer directions.

The provider may return fewer valid directions, but the graph must not retain more than the caller's explicit bound.

### Vertical

**Vertical** describes how deeply a thought is developed through successive levels of more-specific reasoning.

For explicit control:

```python
vertical=8
```

means:

> Permit development up to eight generated child levels beneath the root, using the package's documented graph-level semantics.

Vertical development may branch internally. "Vertical" therefore describes depth, not a guarantee of a single linear chain.

The number of children produced during an individual vertical expansion is an orchestration or generation-policy concern. It must not be implicitly determined by the public `horizontal` value.

### Progression Type

`progression_type` remains a vertical semantic control.

It describes the intended relationship among vertically generated thoughts, such as implementation steps, simple-to-complex progression, chronology, problem/solution, or prerequisite/dependency.

It must not control:

- horizontal breadth;
- vertical depth;
- exploration intensity;
- stopping behavior;
- graph traversal;
- provider budgets.

## Explicit Mode

Advanced callers must be able to control horizontal and vertical bounds independently.

Conceptually:

```python
generate_thought_graph(
    concept,
    horizontal=2,
    vertical=8,
)
```

The semantics are:

- `horizontal=n`: retain at most `n` root-level peer directions;
- `vertical=n`: permit at most `n` generated child levels beneath the root;
- horizontal and vertical are independent;
- `horizontal` must not silently become the child count for every vertical expansion;
- explicit values define deterministic orchestration bounds;
- explicit mode does not use adaptive semantic stopping to reduce the caller's requested traversal bound, except when generation naturally returns no usable children or an internal safety guard must terminate execution.

The public contract should be **maximum / at most**, not **exactly**. Exact output cardinality cannot be guaranteed across providers and is not currently structurally enforced.

## Adaptive Exploration

Adaptive behavior should not expose separate `horizontal="auto"` and `vertical="auto"` controls as the normal interface.

Instead, normal callers should use a single **exploration profile** that tells the orchestration layer how aggressively to explore the concept.

Recommended profiles:

```text
focused
balanced
rich
```

`balanced` should be the normal default.

Conceptually:

```python
generate_thought_graph(concept)
```

is equivalent to balanced adaptive exploration.

A caller may request:

```python
generate_thought_graph(
    concept,
    exploration="focused",
)
```

or:

```python
generate_thought_graph(
    concept,
    exploration="rich",
)
```

### Exploration Is a Policy, Not a Hidden Count

Exploration profiles must not simply map to fixed graph dimensions such as:

```text
focused  -> horizontal=1, vertical=3
balanced -> horizontal=2, vertical=6
rich     -> horizontal=3, vertical=10
```

That would turn adaptive exploration into disguised static configuration.

Instead, the profile changes the engine's willingness to continue exploring.

The engine should evaluate marginal conceptual value as the graph develops.

### Focused

Focused exploration should prefer the smallest graph that adequately develops the concept.

It should require relatively strong additional value before:

- opening another horizontal direction;
- continuing another vertical level;
- retaining additional branches.

### Balanced

Balanced exploration should continue while additional reasoning provides clear conceptual value.

It should provide useful coverage and depth without aggressively pursuing marginal distinctions.

### Rich

Rich exploration should pursue subtler distinctions, broader useful coverage, and deeper decomposition when those additions remain meaningful.

Rich does **not** mean "always generate more" and does not imply a fixed depth or breadth. It should still stop naturally when further generation becomes repetitive, trivial, excessively narrow, or otherwise low-value.

## Adaptive Horizontal Behavior

During adaptive exploration, horizontal generation should answer:

> Is another materially distinct peer direction useful?

The engine should stop opening new horizontal directions when additional candidates mostly:

- overlap existing directions;
- restate an existing direction;
- represent details that belong underneath an existing thought;
- add insufficient marginal coverage.

The exploration profile determines how much marginal value is required to continue.

Horizontal exploration should remain naturally narrow when the concept does not warrant multiple peer directions. A valid adaptive result may contain only one horizontal direction.

## Adaptive Vertical Behavior

During adaptive exploration, vertical generation should answer:

> Does developing this thought another level still add meaningful conceptual value?

Vertical depth should not be selected once at the beginning and then traversed blindly.

The engine should evaluate continuation as generation proceeds. It should stop a branch when another level would mostly:

- restate existing content;
- add trivial detail;
- over-specialize without meaningful conceptual gain;
- violate the intended progression;
- continue beyond a natural conceptual endpoint.

Different branches may stop at different depths.

The exploration profile changes the stopping policy:

- focused requires stronger marginal value to continue;
- balanced continues on clear additional value;
- rich permits subtler but still meaningful additional value.

The exact thresholds or judging mechanics are implementation details and should not be exposed as ordinary public API parameters.

## Branching During Vertical Development

Vertical depth and vertical branching are separate implementation concerns.

The public API should not introduce confusing concepts such as `vertical_width`.

When one thought is expanded vertically, the generation primitive may return multiple direct children. The orchestration layer is responsible for deciding which children are useful to retain and which branches merit further development.

The public `horizontal` setting applies to horizontal peer directions and must not be reused as the per-node child limit during vertical expansion.

Adaptive exploration must also avoid expanding every branch mechanically when doing so adds little value. Branch selection and pruning are part of exploration policy.

## Internal Safety Limits

Removing public maximums does **not** mean execution should be literally unbounded.

The engine must retain internal safeguards against pathological graph growth, runaway recursion, excessive provider calls, excessive node counts, excessive token or cost consumption, and unreasonable execution time.

These safeguards are distinct from semantic stopping:

```text
semantic stopping
    The exploration policy decides that further thought adds insufficient value.

safety stopping
    The engine terminates execution because an internal operational guard has been reached.
```

Ordinary callers should not be required to configure:

- `max_horizontal`;
- `max_vertical`;
- novelty thresholds;
- stopping thresholds;
- provider-call budgets;
- total-node budgets.

Those are internal implementation and operational concerns unless a future advanced API demonstrates a concrete need to expose them.

When an internal safety guard terminates an adaptive run, the result should expose enough diagnostic information to distinguish a safety stop from a natural semantic stop.

## Recommended Public API

The desired conceptual API is:

```python
generate_thought_graph(
    concept,
    exploration="balanced",
)
```

with optional explicit mode:

```python
generate_thought_graph(
    concept,
    horizontal=2,
    vertical=8,
)
```

The exact signature should avoid ambiguous combinations.

A caller should not simultaneously specify an adaptive exploration profile and explicit horizontal/vertical controls unless a future requirement defines clear semantics for that combination.

A clean contract is:

```text
adaptive mode
    concept + exploration

explicit mode
    concept + horizontal + vertical
```

The implementation may preserve existing parameters for backward compatibility while presenting this clearer contract through a new or versioned concept-first entry point.

The existing typed `generate(HorizontalGenerationRequest)` and lower-level `expand(...)` APIs must remain backward compatible.

## Ownership

### Existing Generation Primitives

The existing provider-facing horizontal and vertical generation primitives should remain focused on:

- receiving a generation request;
- rendering the appropriate prompt;
- invoking the provider;
- parsing and validating the provider response.

They should not become responsible for global exploration policy.

### Thought Graph Orchestration

`ThoughtGraphEngine` is the natural initial owner for the new behavior because it already owns:

- root construction;
- graph traversal;
- recursive expansion;
- graph limits;
- argument validation;
- result construction.

The first implementation should modify orchestration rather than rewrite the underlying generation primitives.

In particular, the current coupling in which one breadth value controls both root horizontal generation and vertical child batches must be removed.

### Exploration Policy Abstraction

Do not introduce a substantial planner or policy framework merely to support explicit horizontal and vertical controls.

Adaptive exploration will require decision logic for:

- horizontal continuation;
- vertical continuation;
- branch selection and pruning;
- exploration-profile behavior;
- stop reasons;
- internal safety budgets.

Begin with the smallest orchestration implementation that keeps these responsibilities clear.

Extract a dedicated exploration-policy object only when this logic becomes sufficiently stateful or substantial that keeping it inside `ThoughtGraphEngine` harms clarity or testability.

If extracted, the policy should answer questions such as:

```text
Should another horizontal direction be explored?
Should this branch continue vertically?
Which generated branches remain worth exploring?
Why did exploration stop?
```

It should not own prompt rendering, provider adapters, response parsing, or graph mutation.

## Compatibility Requirements

- Existing `generate(HorizontalGenerationRequest)`, `expand`, `expand_all`, `generate_subtopics`, `expand_subtopic`, and `generate_thought_graph` calls must continue to work unless changed through an explicit versioned API decision.
- `progression_type` remains vertical-only and continues accepting its current enum and compatible raw strings.
- Existing provider adapters and provider-neutral generation contracts should remain unchanged unless implementation evidence demonstrates a concrete need.
- Existing prompt overrides and provider injection behavior must remain supported.
- Legacy pipeline wrappers should continue delegating to canonical thought-generation APIs and must not gain a second exploration-policy implementation.
- Explicit mode must remain available for deterministic tests, benchmarks, and advanced callers.
- Adaptive exploration should not silently change the semantics of existing explicit calls.

## Test Requirements

Tests should cover:

- independent explicit horizontal and vertical values, including asymmetric cases such as `horizontal=2, vertical=8`;
- verification that horizontal values are not reused as vertical child-count limits;
- exact mapping of explicit vertical values to graph levels, including off-by-one cases;
- explicit-mode graph shape and provider invocation order with deterministic fake providers;
- focused, balanced, and rich exploration behavior using deterministic policy/provider test doubles;
- adaptive horizontal continuation and stopping for distinct, overlapping, synonymous, and too-narrow candidates;
- adaptive vertical continuation and natural endpoint stopping;
- branches stopping at different vertical depths;
- adaptive branch selection and pruning;
- empty-child natural stopping;
- internal safety-guard termination;
- diagnostic distinction between semantic stops and safety stops;
- `progression_type` affecting vertical semantics only;
- provider portability through provider-neutral contracts;
- backward compatibility with existing concept-first and package-level tests.

Tests for exploration profiles should verify policy behavior rather than depend on fixed hidden breadth/depth numbers.

For example, a rich-profile test should establish that a marginal-but-meaningful continuation is retained where focused mode stops. It should not assert that rich always produces a particular depth.

## Phased Roadmap

### Phase 1 — Decouple Explicit Horizontal and Vertical Controls

Add the smallest concept-first API behavior necessary for independent explicit horizontal and vertical bounds.

Break the current coupling between root horizontal breadth and the child count used during vertical expansion.

Define and test:

```python
horizontal=2
vertical=8
```

without changing the provider-facing generation primitives unnecessarily.

Add graph-shape, validation, and provider-call tests.

Do not introduce adaptive exploration in this phase.

### Phase 2 — Adaptive Exploration Profiles

Add:

```text
focused
balanced
rich
```

with balanced as the normal adaptive default for the new API.

Implement adaptive horizontal and vertical continuation decisions in orchestration.

Profiles should alter continuation and stopping behavior, not map to fixed breadth/depth presets.

Add deterministic tests for profile behavior, branch-specific stopping, and material-distinctness decisions.

### Phase 3 — Branch Selection, Diagnostics, and Safety Budgets

Refine adaptive traversal so the engine does not mechanically expand every generated branch.

Add:

- branch selection and pruning;
- explicit semantic stop reasons;
- internal call/node/token/runtime safeguards as appropriate;
- diagnostics that distinguish semantic stopping from safety stopping.

Keep these operational safeguards out of the normal public API.

### Phase 4 — Extract Exploration Policy if Warranted

Evaluate the orchestration after Phases 2 and 3.

If adaptive decision state, branch selection, budget accounting, and stop diagnostics have made `ThoughtGraphEngine` too stateful or difficult to test, extract a small dedicated exploration-policy abstraction.

Do not perform this extraction merely for architectural symmetry.

Use benchmarks and behavior tests to refine focused, balanced, and rich semantics without converting them into fixed graph dimensions.

## Open Design Questions

1. Should the new concept-first public method remain `generate_thought_graph`, or should a new clearer entry point be introduced while the existing method remains compatibility-facing?
2. Should explicit mode require both `horizontal` and `vertical`, or may callers explicitly control one while allowing the engine to choose the other?
3. What internal signal or judge should determine material distinctness for horizontal continuation?
4. What internal signal or judge should determine marginal conceptual value for vertical continuation?
5. Should adaptive continuation decisions be made per node, per frontier, or through a hybrid strategy?
6. How should the engine select promising branches without turning exploration into a ranking-only problem?
7. Which internal operational safeguards are necessary for the first adaptive release?
8. What result metadata is necessary to distinguish natural semantic stops, empty-provider stops, provider failures, and internal safety stops?
9. Should adaptive stop decisions be persisted in graph metadata or remain execution diagnostics?
10. At what point does adaptive orchestration justify extracting a dedicated exploration-policy object?
