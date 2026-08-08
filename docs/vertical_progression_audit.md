# Vertical Thought Progression Audit

## 1. Executive Summary

The repository currently contains exactly five progression labels:

1. `implementation_steps`
2. `simple_to_complex`
3. `chronological`
4. `problem_solution`
5. the former generic child-expansion behavior

They do not form one coherent, validated progression system today.

`implementation_steps` is the default for the lower-level
`VerticalGenerationRequest`; `simple_to_complex`, `chronological`, and
`problem_solution` are described in the lower-level vertical prompt; and
the generic child-expansion behavior was hardcoded by the public concept-first façade. The public
graph path does not expose a progression argument and does not consume the
progression placeholder in the lower-level prompt.

The largest inconsistency is architectural:

```text
lower-level engine.expand()/expand_all()
    -> progression_type is passed into VERTICAL_SUB_THOUGHT_GENERATION_PROMPT

public generate_thought_graph()/expand_subtopic()
    -> a generic child-expansion mode was hardcoded
    -> CONCEPT_DETAIL_GENERATION_PROMPT does not consume it
```

The current graph behavior is best described as **generic direct-child
expansion with refinement and decomposition tendencies**, not as an explicitly
chosen taxonomy relation. The lower-level path is a step-by-step explanatory
prompt with mixed procedural, conceptual, temporal, and problem-solving modes.

The safest recommendation is to preserve all five strings, keep omitted public
graph calls on the existing generic child-expansion behavior, and avoid presenting
future names such as `decomposition` or `temporal` as implemented features.
Before adding a new taxonomy, the two vertical paths should be deliberately
separated or unified behind one normalized, provider-independent prompt
contract.

For workflow requirements, the current set is useful but incomplete. It covers
procedural steps, sequence, problem-to-resolution movement, generic child
expansion, and conceptual elaboration. A clearly defined prerequisite/
dependency relation is the main potentially missing workflow relationship, but
it should not be added until its direction is specified.

No production code, prompt, model, or test was changed for this audit.

## 2. Current Progression Types in the Repository

### `implementation_steps`

**Exact value:** `"implementation_steps"`.

**Locations and role:**

- `src/bot0_thought_graph/thought_generation/engine.py:90` — default value of
  `VerticalGenerationRequest.progression_type`.
- `engine.py:262` — default value of `ThoughtGraphEngine.expand_all()`.
- `src/bot0_thought_graph/thought_generation/expansion.py:16,48` — defaults of
  `expand_vertical()` and `expand_idea()`.
- `src/bot0_thought_graph/prompts/thought_generation_prompt_templates.py:201`
  — documented prompt option.
- `README.md` — lower-level usage example.

It is the default lower-level mode and is passed into the legacy vertical
prompt. The prompt meaning is “key areas or steps one would need to consider
when implementing or working with the main thought.” Its direction is parent
thought -> implementation-oriented steps or areas, but strict ordering and
prerequisite semantics are not required by the prompt.

It is primarily workflow- and implementation-oriented. It is reachable through
`engine.expand()` and `engine.expand_all()`, but not through the public
concept-first graph façade. The prompt does change behavior because the value
is interpolated, but there is no enum or validation. It is not retained in any
result model.

### `simple_to_complex`

**Exact value:** `"simple_to_complex"`.

**Location and role:** It appears at
`src/bot0_thought_graph/prompts/thought_generation_prompt_templates.py:200`
in the lower-level prompt's progression list. It is a prompt option only: not
a default, enum, validator, or Python branch.

The prompt says to start with basic concepts and gradually introduce more
advanced ideas. Its direction is lower conceptual complexity -> higher
conceptual complexity. It is primarily conceptual and explanatory, not
necessarily a hierarchy of constituent parts. It is reachable through
`engine.expand()`/`VerticalGenerationRequest`, not through the graph façade.
The interpolated text changes the lower-level prompt, but the value is not
validated or retained in result models.

### `chronological`

**Exact value:** `"chronological"`.

**Location and role:** It appears at
`src/bot0_thought_graph/prompts/thought_generation_prompt_templates.py:203`
in the lower-level prompt's progression list. It is a prompt option only.

The prompt means explaining the evolution or historical development of a
thought, “if applicable.” Its direction is earlier event/state -> later
event/state, but it does not require a strict next-step workflow. It is
primarily temporal and workflow-oriented. It is lower-level-only, changes the
prompt through interpolation, is not validated, and is not retained in result
models.

### `problem_solution`

**Exact value:** `"problem_solution"`.

**Location and role:** It appears at
`src/bot0_thought_graph/prompts/thought_generation_prompt_templates.py:204`
in the lower-level prompt's progression list. It is a prompt option only.

The prompt says to introduce problems or challenges related to the main thought
followed by solutions or approaches. Its direction is ambiguous: it may be
problem -> solution, or a sequence mixing problem analysis and solutions. The
prompt does not require that every child be a solution or define problem and
solution roles. It is primarily problem-solving and workflow-oriented. It is
lower-level-only, prompt-interpolated, unvalidated, and not retained in result
models.

### Former generic child-expansion behavior

**Locations and role:**

- `src/bot0_thought_graph/thought_generation/engine.py:655` — hardcoded by
  `_expand_subtopic_result()`.
- `README.md` — described as the façade mode in the lower-level example.

This was the public concept-first façade's implicit mode. It was not listed in
the lower-level prompt's four documented options. The façade selects
`CONCEPT_DETAIL_GENERATION_PROMPT`, which does not contain a
`{progression_type}` placeholder, so the former generic child-expansion label did not
change that prompt.

Its actual semantics are generic direct-child expansion with a refinement bias:
children must be more specific than the parent, remain in the root concept,
have consistent granularity, and avoid unrelated sibling-level dimensions.
That also permits loose decomposition, but it does not require constituent
parts, narrower subtypes, implementation steps, consequences, or next stages.

It is a conceptual/hierarchical and generic relation, implicitly used by
`expand_subtopic()` and recursive `generate_thought_graph()` expansion. The
label is not retained in `Thought`, `ThoughtNode`, or `ThoughtGraph`.

## 3. Current Code Locations and Call Paths

### Lower-level vertical path

```text
ThoughtGraphEngine.expand(VerticalGenerationRequest)
    -> thought_generation.expansion.expand_vertical()
        -> VERTICAL_SUB_THOUGHT_GENERATION_PROMPT
        -> format progression_type, idea, thought, and num_sub_thoughts
        -> provider.generate(GenerationRequest)
        -> parse_thought(result.text)
```

`engine.expand_all()` calls `expand_idea()`, which invokes the same vertical
function once per top-level thought. The lower-level default is
`implementation_steps`; callers can pass any string, including the other
three prompt-described values.

### Public graph path

```text
ThoughtGraphEngine.generate_thought_graph()
    -> validate concept, depth, breadth
    -> generate_array_of_thoughts()
        -> generate(HorizontalGenerationRequest)
            -> generate_horizontal()
                -> horizontal prompt -> provider -> parse_idea()
    -> create root ThoughtNode and first-level children
    -> _expand_graph_node() recursively
        -> _expand_subtopic_result()
            -> generic child-expansion mode
            -> CONCEPT_DETAIL_GENERATION_PROMPT
            -> expand(VerticalGenerationRequest)
                -> expand_vertical()
                -> provider -> parse_thought()
            -> convert sub-thoughts to ThoughtNode children
```

`depth=1` creates the root and first horizontal layer. At deeper levels,
`_expand_graph_node()` expands each node until the configured depth. `breadth`
controls requested and retained children at every expansion.

Relevant files are:

- `thought_generation/engine.py` — façade, request dataclass, and recursion.
- `thought_generation/expansion.py` — provider-independent vertical call.
- `prompts/thought_generation_prompt_templates.py` — both vertical prompts.
- `models/thought_models.py` — `Thought`, `ThoughtArray`, `ThoughtNode`, and
  `ThoughtGraph`.
- `tests/test_concept_first_api.py` — façade prompt/graph structure tests.
- `tests/test_thought_generation_package.py` — lower-level expansion tests.
- `docs/public_api.md` and `README.md` — current API documentation.

## 4. Current Semantic Behavior

The repository has two semantic conventions rather than one.

The lower-level convention asks for a step-by-step explanation that follows a
free-form `progression_type`. Its documented options mix implementation,
conceptual complexity, chronology, and problem-solving. The prompt does not
create typed edges or validate the option.

The public graph convention asks for direct child details that are more
specific than the parent. It is a generic hierarchy with refinement and loose
decomposition tendencies. It is not causal, temporal, or problem-solution by
default.

## 5. Current Type Comparison

| Current type | Meaning in current code | Direction | Publicly selectable? | Workflow relevance | Main issue |
| --- | --- | --- | --- | --- | --- |
| `implementation_steps` | Areas or steps for implementing/working with a thought | Parent -> implementation steps/areas; strict order not required | Lower-level only | High for procedures and requirements | “Steps” sounds ordered, but prerequisites are not defined |
| `simple_to_complex` | Basic concepts followed by advanced concepts | Lower conceptual complexity -> higher complexity | Lower-level only | Moderate for staged explanation | Complexity is not necessarily a domain parent-child edge |
| `chronological` | Evolution or historical development, if applicable | Earlier state/event -> later state/event | Lower-level only | High for process/lifecycle analysis | No ordering validation; history is broader than “next” |
| `problem_solution` | Problems/challenges followed by solutions/approaches | Ambiguous problem -> solution or mixed sequence | Lower-level only | High for incidents and remediation | Problem, cause, and solution roles are not defined |
| former generic child expansion | Direct child details more specific and in scope | Parent -> generic direct child detail | Former implicit public default | High for immediate sub-processes/details | Hardcoded and not consumed by its selected prompt |

None is an enum or validated allowed value. None survives into package-owned
result models.

## 6. Public Façade vs Lower-Level Progression System

This split may have started intentionally—one API explains a thought in a
progression, while the other builds a generic hierarchy—but the current code
does not document or enforce that boundary. The evidence more strongly
resembles historical drift:

- the lower-level request has a semantic field and default;
- the prompt has four unrelated mode labels;
- the façade introduces a fifth label;
- the façade chooses a prompt that ignores that fifth label; and
- tests verify structure and parsing, not semantic mode behavior.

The public graph path should therefore not be assumed to support all lower-level
modes merely because the dataclass field exists.

## 7. Workflow Requirements Analysis

### `implementation_steps`

Best current answer to “How is this carried out?” for business processes,
clinical workflows, operations, manufacturing, incidents, and requirements
implementation. It may produce actionable areas or steps, but the prompt does
not guarantee order, prerequisites, actors, branching, or executable process
semantics.

### `chronological`

Best current answer to “What happens next?” It is useful for clinical,
operational, manufacturing, and incident workflows. The prompt actually says
historical/evolutionary development, so a future workflow contract should
clarify strict next-stage sequencing.

### `problem_solution`

Useful for “What problem leads to what resolution?” in incidents, requirements
gaps, and remediation. The prompt allows mixed challenges and solutions, so it
does not yet provide a reliable problem -> resolution edge or a causal claim.

### Former generic child-expansion behavior

Useful for breaking an immediate workflow or process into sub-processes/details.
It is the safest current recursive graph mode because it asks for generic
hierarchical children rather than a sequence or transition.

### `simple_to_complex`

Useful for elaborating a workflow or requirements model from overview to
actors, exceptions, controls, and implementation detail. It is not a reliable
process-order mode; its children may be explanatory stages rather than actual
workflow nodes.

### Overall sufficiency

The five are useful for basic workflow discovery, but they do not rigorously
represent prerequisites, dependencies, branching, parallelism, joins, or
validated causal claims. The main missing workflow relationship is a
directionally explicit prerequisite/dependency relation.

## 8. Semantic Overlap and Ambiguity in the Current Five

### `implementation_steps` vs `chronological`

They are not inherently identical. `implementation_steps` asks which areas or
steps are needed to implement/work with a thought; it does not explicitly say
“next” or “after.” `chronological` asks for evolution/history and implies
order, but not necessarily actionable implementation. They overlap when an
implementation is sequential, but the current prompt does not guarantee that.

### `simple_to_complex` vs former generic child expansion

`simple_to_complex` is ordered conceptual elaboration. Former generic child
expansion is a
set of direct, more-specific details. Both may increase detail, but only
Former generic child expansion is a conventional hierarchy edge. A simple-to-complex result
may be an explanatory sequence rather than siblings at one ontology level.

### `problem_solution` directionality

The current prompt does not define whether the parent is always a problem,
whether every child is a solution, or whether children may be causes/problem
analyses. It is a problem-solving progression, not a consistently typed
parent-child relation.

### Former generic child expansion: decomposition vs refinement

The code supports neither exclusively. “More specific” supports refinement;
distinct details and the general “break down” framing support decomposition.
Because the prompt does not say “constituent part” or “narrower subtype,” the
accurate current description is a generic child-expansion hybrid.

## 9. Current Graph-Edge Semantics

`ThoughtGraph` stores every relation as an untyped `ThoughtNode.children` edge.
There is no edge type, event order, causal confidence, prerequisite marker, or
problem/solution role. The model stores only `concept`, `root`, `depth`, and
`breadth` at graph level.

The current labels therefore imply different edge families:

```text
former generic mode   -> generic hierarchical child edge
implementation_steps -> procedural/implementation edge
chronological        -> sequence or historical edge
problem_solution     -> problem-solving transition edge
simple_to_complex    -> explanatory conceptual progression edge
```

Representing all of them in one untyped tree is convenient, but it can mislead
consumers into treating a sequence or transition as a decomposition child.
Typed edge provenance is an architectural implication, not something to add
silently in this audit.

## 10. Gaps in the Existing Progression Set

The current values cover many common workflow questions, so additions should
be justified by a missing relation rather than taxonomy aesthetics.

The clearest missing workflow relation is **prerequisite/dependency**. For
example, a workflow may need to express that eligibility verification is a
prerequisite for enrollment. `implementation_steps` may mention this, but does
not guarantee it and does not define whether “parent requires child” or “child
requires parent” is the direction.

`causal` is also not guaranteed. `problem_solution` may produce a transition
from issue to resolution, but it does not define causal direction; chronology
does not imply causality. Evidence, abstraction, and contrast are not required
for the basic workflow use case: evidence needs provenance, abstraction moves
upward, and contrast is usually horizontal.

## 11. Possible Future Normalization

Everything in this section is **PROPOSED / NOT IMPLEMENTED**.

| Proposed name | Relation to current values | Future treatment |
| --- | --- | --- |
| `temporal` | Could be a clearer public name for `chronological` | Alias only if strict process order, rather than history, is intended |
| `implementation` | Short form of `implementation_steps` | Possible convenience alias; never remove the current value |
| `decomposition` | Overlaps with some former generic child-expansion results | Possible explicit submode, not an exact alias |
| `refinement` | Describes the “more specific” part of former generic child expansion | Possible explicit submode, not an exact alias |
| `causal` | Not guaranteed by any current label; adjacent to `problem_solution` | Genuinely new if directional effects are needed |
| `abstraction` | Reverse of refinement; no current equivalent | Separate upward/generalization operation |
| `dependency` / `prerequisite` | Not guaranteed by `implementation_steps` or `chronological` | Genuinely missing for rigorous workflow graphs |
| `goal_means` | May be approximated by implementation steps | Application-specific; do not merge silently |
| `evidence` | No current equivalent | Future argument/evidence graph |
| `diagnostic` | May overlap with problem-solution analysis | Specialized inverse-causal mode |
| `contrast` | No suitable vertical equivalent | Better modeled as horizontal comparison |

`decomposition` and `refinement` are best understood initially as possible
submodes of the former generic child-expansion behavior, not replacements for the five current
strings.

## 12. Backward Compatibility

Existing lower-level callers using all four prompt labels must continue to work:

```text
implementation_steps
simple_to_complex
chronological
problem_solution
```

Existing public graph callers implicitly received generic child-expansion behavior.
If a future public argument is added, omission should preserve that exact
behavior:

```text
progression_type=None -> current explicit implementation_steps behavior
```

It should not silently map to `decomposition`, because current direct-child
results are not guaranteed to be constituent parts. Explicit future aliases
such as `temporal -> chronological` or `implementation -> implementation_steps`
are acceptable only if prompt behavior is equivalent. Existing values should
not be silently removed or renamed.

## 13. Public API Options

A conservative future façade API would be:

```python
graph = engine.generate_thought_graph(
    topic="clinical research participant recruitment",
    depth=3,
    breadth=5,
    progression_type="implementation_steps",
)
```

Recommendation:

- Make omission/`None` preserve the current explicit `implementation_steps` path.
- Keep all five strings available to the lower-level API for compatibility.
- Do not initially expose every lower-level mode to recursive graph generation
  until sequence and transition edges are deliberately specified.
- If `implementation_steps` or `chronological` later become graph options,
  document that the result remains a generic tree without typed workflow edges.

A string-backed enum or `Literal` could be introduced later, but no enum exists
today and none should be added during this audit.

## 14. Prompt Architecture Implications

The lower-level prompt already consumes `{progression_type}`, but its four
labels are merely natural-language options. The public concept-detail prompt
does not consume the former generic child-expansion label.

A later implementation should centralize a progression instruction after the
parent/context fields and before the JSON schema:

```text
existing vertical prompt
    + selected progression instruction
    + parent thought and root concept
    + requested breadth
    + existing JSON schema
```

It should not create provider-specific prompts. Before unifying prompts, decide
whether the graph supports only hierarchical child expansion or also
procedural, sequence, and problem-solving transitions.

Current prompt guidance, summarized without changing it:

- `implementation_steps`: implementation/work steps or areas;
- `simple_to_complex`: basic concepts followed by advanced concepts;
- `chronological`: historical/evolutionary progression;
- `problem_solution`: problems/challenges followed by solutions/approaches;
- `implementation_steps`: implementation details within the parent concept.

## 15. Testing Gaps

Current tests cover structural behavior, not semantic progression behavior.

`tests/test_concept_first_api.py` checks direct-child prompt text, graph depth,
breadth, recursion, and tree structure. `tests/test_thought_generation_package.py`
checks lower-level expansion, parsing, and ordering, but does not assert a
progression label or mode-specific instruction. No current test enumerates the
five labels, rejects invalid values, or checks graph propagation.

Before implementation, deterministic tests should use a fake provider that
records prompts and returns valid fixed JSON. They should verify:

1. all five exact current labels remain accepted where currently supported;
2. `implementation_steps` remains the lower-level default;
3. each lower-level prompt option changes the expected instruction text;
4. `implementation_steps` is the explicit public façade default;
5. omitted future public selection preserves the current prompt;
6. graph recursion propagates one selected mode if graph modes are enabled; and
7. result shape remains the package-owned `ThoughtGraph` model.

Later live tests should evaluate relations rather than exact strings:

- `implementation_steps`: actionable implementation areas/steps;
- `simple_to_complex`: increasing conceptual complexity;
- `chronological`: defensible order;
- `problem_solution`: distinguishable problem and solution roles;
- `implementation_steps`: direct, in-scope implementation details.

## 16. Recommended Next Step

The smallest next implementation should not add a new taxonomy. First decide
whether lower-level sequence/procedure/problem-solving modes are intended for
recursive `ThoughtGraph` generation. Preserve all five exact strings, make the
public default explicit as `implementation_steps`, and add
deterministic propagation tests before changing prompt text.

## 17. Final Recommendation

- **Current types that should remain:** all five exact strings.
- **Lower-level-only types today:** `implementation_steps`,
  `simple_to_complex`, `chronological`, and `problem_solution`.
- **Public façade type today:** `implementation_steps`, explicitly used by
  `expand_subtopic()` and recursive `generate_thought_graph()`.
- **Main overlaps:** `implementation_steps`/`chronological` can both look like
  workflow sequences; `simple_to_complex`/generic child expansion can both add detail;
  generic child expansion itself mixes refinement and decomposition tendencies;
  `problem_solution` has unclear direction.
- **Genuinely missing potential workflow type:** prerequisite/dependency;
  causal is also not guaranteed by the current five.
- **Public graph default:** use explicit `implementation_steps` behavior when
  progression is omitted.
- **Recursive graph support:** do not assume every current type is suitable.
  `implementation_steps` is the explicit current graph mode; the others need explicit
  edge semantics or documented generic-tree limitations.

The actual progression system today is a compatible lower-level prompt
selector plus a separate public direct-child graph path, not one unified
taxonomy.
