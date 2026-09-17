# Interview Package Extraction Requirements

> **Status: authoritative for the end state.**
>
> This document supersedes earlier long-term architecture assumptions,
> including `reusable_disaggregation_package_audit.md` (retained as
> current-state evidence) and any target layout that retains
> `bot0_thought_graph/interview/`. See also
> `reusable_thought_graph_target_architecture.md` (summary).

## Status

Proposed architecture requirement.

This document defines the target removal of interview-specific
functionality from `bot0_thought_graph`.

It supersedes any earlier long-term architecture assumption that
`bot0_thought_graph/interview/` should remain as an optional subsystem
inside the reusable thought-graph package.

------------------------------------------------------------------------

## 1. Goal

`bot0_thought_graph` should be a reusable Python package for
complex-topic disaggregation and thought-graph generation.

It should own the capabilities required to:

-   generate a structured thought graph from a root concept;
-   perform horizontal exploration;
-   perform recursive vertical decomposition;
-   evaluate whether further decomposition is worthwhile;
-   interact with supported LLM providers;
-   represent graph/domain contracts;
-   persist graph-related data where required.

It should **not** own conversational interview workflows.

Interview functionality should live in a separate package or application
that may depend on `bot0_thought_graph`.

------------------------------------------------------------------------

## 2. Target Dependency Direction

Desired:

``` text
interview/application package
            |
            | depends on
            v
    bot0_thought_graph
            |
    +-------+--------+
    |       |        |
    v       v        v
 thought  reflection providers
 generation
```

Prohibited:

``` text
bot0_thought_graph
        |
        v
interview/application
```

Core thought-graph generation must not import interview-specific code.

------------------------------------------------------------------------

## 3. Target Package Boundary

The intended long-term package shape is:

``` text
src/
└── bot0_thought_graph/
    ├── __init__.py
    ├── thought_generation/
    ├── reflection/
    ├── providers/
    ├── models/
    ├── prompts/
    └── storage/
```

There should be no permanent:

``` text
bot0_thought_graph/interview/
```

namespace.

A consuming interview package/application may contain capabilities such
as:

``` text
interview_package/
├── question_generation/
├── answer_evaluation/
├── policy/
└── orchestration/
```

and may call `bot0_thought_graph` through its public API.

------------------------------------------------------------------------

## 4. Responsibility Rule

Code belongs in `bot0_thought_graph` only when it is part of reusable
thought-graph/disaggregation behavior or infrastructure required
directly by that behavior.

Code does **not** belong in `bot0_thought_graph` merely because:

-   it uses an LLM;
-   it evaluates text;
-   it historically lived beside thought generation;
-   it is used by an interview workflow;
-   an "agent" happens to call thought-graph functionality.

Organize by responsibility, not by agent identity.

------------------------------------------------------------------------

## 5. Known Ownership

The existing reflection audit established:

``` text
decomposition.py
    core thought-generation reflection

shared.py
    shared reflection/provider infrastructure

answer_evaluation.py
    interview-specific

policy.py
    interview-specific
```

Therefore:

-   `decomposition.py` belongs in package-level `reflection/`;
-   reusable infrastructure from `shared.py` belongs in package-level
    `reflection/` or another core infrastructure namespace if later
    evidence warrants it;
-   `answer_evaluation.py` does not belong in the final
    `bot0_thought_graph` package unless a separate audit proves that
    part of it is actually generic core infrastructure;
-   `policy.py` does not belong in the final `bot0_thought_graph`
    package unless a separate audit proves otherwise.

------------------------------------------------------------------------

## 6. Required Audit Before Removal

Do not delete `interview/` wholesale without first auditing its actual
dependency surface.

Inventory all files under:

``` text
src/bot0_thought_graph/interview/
```

For each file or capability classify it as:

``` text
core thought-graph responsibility
    -> migrate to the correct bot0_thought_graph namespace

interview/application responsibility
    -> extract to the consuming package/application

obsolete or superseded
    -> remove

compatibility-only surface
    -> retain temporarily only if justified
```

Also identify:

-   imports from core package code into `interview`;
-   imports from tests into `interview`;
-   root-package exports such as `InterviewEngine`;
-   examples/scripts depending on interview APIs;
-   documentation describing interview as part of the package;
-   packaging configuration that exposes interview modules;
-   compatibility requirements for existing callers.

Persist the audit before destructive cleanup.

------------------------------------------------------------------------

## 7. Reflection Migration Prerequisite

Before removing `interview/`, complete the package-level reflection
migration:

``` text
bot0_thought_graph/interview/reflection/decomposition.py
    ->
bot0_thought_graph/reflection/decomposition.py
```

and move reusable shared reflection plumbing out of the interview
namespace.

The core dependency should become:

``` text
thought_generation
        |
        v
    reflection
```

not:

``` text
thought_generation
        |
        v
     interview
        |
        v
    reflection
```

This migration must not change decomposition semantics.

------------------------------------------------------------------------

## 8. Extraction Requirements

Interview-specific behavior that is still useful should be moved to a
separate consuming package/application rather than renamed or relocated
inside `bot0_thought_graph`.

The extraction should preserve clear dependency direction:

``` text
interview package/application
    -> bot0_thought_graph public API
```

The new consumer should not depend on private implementation details
where a stable package API can be provided.

Do not create a new `bot0_thought_graph/agents/` namespace merely to
preserve old interview or agent abstractions.

------------------------------------------------------------------------

## 9. Public API Cleanup

The final `bot0_thought_graph` public API should expose thought-graph
capabilities, not interview orchestration.

The existing root export:

``` python
from bot0_thought_graph import InterviewEngine
```

is transitional and should not be part of the desired final API.

Before removal:

1.  identify all internal and external compatibility expectations
    represented in the repository;
2.  decide whether a temporary deprecation/re-export shim is justified;
3.  document any intentional breaking change;
4.  remove eager or lazy loading of interview infrastructure from the
    graph package once compatibility obligations are resolved.

The target root import should load only thought-graph functionality and
its core dependencies.

------------------------------------------------------------------------

## 10. Compatibility Strategy

Compatibility is subordinate to the package boundary, but migration
should be deliberate.

Possible temporary compatibility mechanisms include:

-   deprecated re-exports;
-   thin forwarding modules;
-   migration documentation.

Do not preserve compatibility indefinitely if doing so requires the
thought-graph package to retain interview implementation.

Any shim must have:

-   a documented purpose;
-   a clear owner;
-   a removal condition;
-   tests proving it does not restore a core dependency on interview
    implementation.

------------------------------------------------------------------------

## 11. Validation Requirements

Before declaring extraction complete, prove that:

-   `import bot0_thought_graph` does not import interview code;
-   `ThoughtGraphEngine` does not import interview code;
-   thought graph generation works with the interview package absent;
-   decomposition reflection works with the interview package absent;
-   provider selection still works;
-   focused/balanced/rich exploration behavior is unchanged except for
    non-semantic import/package effects;
-   existing graph/domain models remain compatible;
-   graph persistence behavior remains compatible;
-   package tests pass from the canonical installable package;
-   a clean external consumer can install and call `bot0_thought_graph`
    without interview dependencies.

Add explicit package-boundary tests where practical.

------------------------------------------------------------------------

## 12. Deletion Criteria

`src/bot0_thought_graph/interview/` may be removed when all of the
following are true:

-   all reusable core capabilities have been migrated to proper package
    ownership;
-   all still-needed interview capabilities have been extracted to their
    consuming package/application;
-   core imports no longer reference `interview`;
-   root package initialization no longer requires interview;
-   compatibility strategy has been implemented or intentionally
    declined;
-   tests/examples/docs have been updated;
-   clean-package validation succeeds.

------------------------------------------------------------------------

## 13. Out of Scope

This extraction must not redesign:

-   horizontal generation semantics;
-   vertical decomposition semantics;
-   decomposition prompts;
-   exploration profiles;
-   traversal rules;
-   graph models;
-   provider adapters;
-   deterministic guards;
-   safety budgets.

Do not tune thought-generation behavior as part of this architecture
cleanup.

------------------------------------------------------------------------

## 14. Implementation Sequence

### Phase A --- Core reflection extraction

Create package-level `reflection/`, move decomposition and reusable
shared reflection plumbing, update imports, and preserve behavior.

### Phase B --- Interview extraction audit

Audit the complete canonical `interview/` surface and all dependencies.
Persist the classification and proposed destinations.

### Phase C --- Extract or retire interview capabilities

Move still-needed interview/application behavior to the separate
consumer. Remove obsolete or superseded behavior.

### Phase D --- Public API and compatibility cleanup

Remove `InterviewEngine` and other interview-specific exports from the
desired graph-package API. Retain only explicitly justified temporary
shims.

### Phase E --- Remove canonical interview namespace

Delete `bot0_thought_graph/interview/` after the deletion criteria are
satisfied.

### Phase F --- External package validation

Install/use `bot0_thought_graph` from a clean external project and
verify thought generation without interview code.

------------------------------------------------------------------------

## 15. End State

The architectural boundary should be simple:

> `bot0_thought_graph` generates and evaluates the structure of thought
> graphs. Conversational/interview workflows that consume those graphs
> belong to separate packages or applications.

The graph package must be independently installable, importable,
testable, and usable without interview infrastructure.
