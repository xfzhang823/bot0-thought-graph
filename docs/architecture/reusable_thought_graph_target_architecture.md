# Reusable Thought Graph Package --- Target Architecture Requirements

> **Status: normative summary.**
>
> This document summarizes the target architecture. The detailed,
> authoritative requirements are in
> `interview_package_extraction_requirements.md`. If the two drift, the
> requirements document wins.

## Status

Updated target architecture.

This document records the desired package boundary after deciding that
interview orchestration is not a responsibility of `bot0_thought_graph`.

For detailed migration requirements, see:

``` text
docs/architecture/interview_package_extraction_requirements.md
```

------------------------------------------------------------------------

## 1. Product Definition

`bot0-thought-graph` is an installable Python package for reusable
complex-topic disaggregation.

Its primary external purpose is conceptually:

``` python
from bot0_thought_graph import generate_thought_graph

graph = generate_thought_graph(
    "hospital emergency department operations",
    exploration="balanced",
)
```

The caller should not need to understand internal traversal, reflection
implementation, provider adapters, legacy pipelines, safety budgets, or
interview/application orchestration.

------------------------------------------------------------------------

## 2. Core Package Responsibilities

The package owns:

### `thought_generation/`

Graph construction and exploration:

-   horizontal thought generation;
-   recursive vertical decomposition;
-   traversal;
-   branch handling;
-   deterministic guards;
-   graph construction.

### `reflection/`

Semantic reflection used by thought generation:

-   decomposition-worthiness evaluation;
-   reusable reflection plumbing directly required by core behavior.

### `providers/`

Provider-neutral LLM infrastructure and provider adapters.

### `models/`

Thought graph and domain contracts.

### `prompts/`

Prompts owned by reusable thought-graph capabilities.

### `storage/`

Persistence owned by thought-graph functionality.

------------------------------------------------------------------------

## 3. Non-Responsibilities

The package does not own:

-   conversational interview orchestration;
-   question-generation workflows whose purpose is conducting an
    interview;
-   interview answer evaluation;
-   interview policy/state progression;
-   facilitator workflows;
-   application-level interview agents;
-   legacy application pipelines.

Those capabilities may consume `bot0_thought_graph` from another package
or application.

------------------------------------------------------------------------

## 4. Target Package Shape

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

The desired final package does not contain:

``` text
bot0_thought_graph/interview/
bot0_thought_graph/agents/
```

unless future requirements establish a new core responsibility that
independently justifies such a namespace.

------------------------------------------------------------------------

## 5. Dependency Direction

Core dependencies should point inward toward reusable package
capabilities.

Example:

``` text
thought_generation
        |
        +------> reflection
        |
        +------> models
        |
        +------> providers
```

External higher-level systems may depend on the package:

``` text
interview application
        |
        v
bot0_thought_graph
```

The reverse dependency is prohibited:

``` text
bot0_thought_graph
        X
        |
        v
interview application
```

------------------------------------------------------------------------

## 6. Reflection Ownership

Decomposition reflection is a core thought-generation capability.

Target:

``` text
bot0_thought_graph/
├── thought_generation/
│   └── ...
└── reflection/
    ├── __init__.py
    ├── decomposition.py
    └── shared.py
```

Core thought generation must import decomposition from package-level
`reflection`, not from an interview namespace.

Interview-specific answer evaluation and policy are not part of the
final package boundary.

------------------------------------------------------------------------

## 7. Interview Extraction

The existing canonical `interview/` tree is transitional.

Do not assume its contents should simply be deleted. Audit each
capability first and classify it as:

-   migrate into a proper core package responsibility;
-   extract into the external interview/application package;
-   remove as obsolete/superseded;
-   retain temporarily as a compatibility shim.

The final goal is removal of the canonical
`bot0_thought_graph/interview/` namespace.

Detailed requirements live in:

``` text
docs/architecture/interview_package_extraction_requirements.md
```

------------------------------------------------------------------------

## 8. Legacy Top-Level `src/` Surfaces

Older parallel surfaces outside the canonical package remain a separate
cleanup concern, including areas such as:

``` text
src/agents/
src/models/
src/prompts/
src/pipelines/
src/thought_generation/
```

Do not move these wholesale into `bot0_thought_graph`.

For each legacy capability determine:

``` text
still used?
   |
   +-- no  -> remove
   |
   +-- yes -> capability already exists canonically?
                 |
                 +-- yes -> remove legacy wrapper when safe
                 |
                 +-- no  -> migrate useful behavior according
                            to actual responsibility
```

An old "agent" does not imply a need for a new canonical `agents/`
namespace.

------------------------------------------------------------------------

## 9. Public API Direction

The desired external API is graph-focused.

Conceptually:

``` python
from bot0_thought_graph import generate_thought_graph
```

`ThoughtGraphEngine` may remain an implementation façade or advanced
API.

Interview-specific root exports such as:

``` python
from bot0_thought_graph import InterviewEngine
```

are transitional and should be removed as part of interview extraction,
subject to an explicit compatibility strategy.

The package root should not eagerly or lazily load interview
implementation in the final architecture.

------------------------------------------------------------------------

## 10. Architectural Invariant

A clean graph-only consumer must be able to:

``` python
import bot0_thought_graph
```

and generate a thought graph without installing, importing, or
understanding an interview subsystem.

This invariant should be protected by tests.

------------------------------------------------------------------------

## 11. Migration Order

Recommended sequence:

(This document enumerates 7 phases; the authoritative requirements document enumerates 6. The requirements document's phase list governs.)

### Phase A

Extract core decomposition reflection from the interview namespace.

### Phase B

Audit the canonical `bot0_thought_graph/interview/` surface for
extraction/removal.

### Phase C

Extract still-needed interview functionality into the consuming
package/application and retire obsolete pieces.

### Phase D

Remove interview-specific public exports and delete the canonical
interview namespace when safe.

### Phase E

Audit and clean the older parallel top-level `src/` legacy architecture
in compatibility-safe waves.

### Phase F

Add the ergonomic graph-focused root API.

### Phase G

Validate package consumption from a clean external environment/project.

------------------------------------------------------------------------

## 12. Scope Protection

Package-boundary work must not be used as an opportunity to change:

-   decomposition semantics;
-   exploration profiles;
-   thought-generation prompts;
-   traversal behavior;
-   graph models;
-   provider behavior;
-   safety budgets.

Architecture cleanup and behavioral tuning are separate concerns.

------------------------------------------------------------------------

## 13. Final Boundary

The intended architecture is:

``` text
                 consuming systems
                /                 \
               v                   v
      interview application    other consumers
                \                 /
                 \               /
                  v             v
                  bot0_thought_graph
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
 thought_generation    reflection      providers
          \               |               /
           +--------------+--------------+
                          |
                          v
                        models
```

The package owns reusable thought-graph generation and the semantic
machinery required to support it.

Higher-level workflows belong above the package, not inside it.
