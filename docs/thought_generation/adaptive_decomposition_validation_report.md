# Adaptive Vertical Decomposition Reflection Validation

Date: 2026-09-16  
Provider/model: DeepSeek `deepseek-chat`  
Configuration: adaptive traversal, same model and progression type (`implementation_steps`) for every run, default internal safety limits, no prompt or threshold tuning.

## Test concepts

- Broad conceptual topic: `climate change adaptation`
- Process/system topic: `hospital emergency department operations`
- Quickly terminal-prone process: `making a cup of tea`
- Meaningful deeper decomposition: `software incident response`
- Additional broad/process coverage: `clinical research participant recruitment`

Each profile was run once for every concept. The harness persisted the complete
tree and metrics as JSON artifacts under `/tmp/decomposition-validation/`.
`expanded` counts vertical-generation calls; retained nodes excludes the root.

## Observed metrics

| Concept | Profile | Max depth | Retained | Expanded | Total calls | Decomp calls | Terminal | Fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clinical research participant recruitment | focused | 3 | 23 | 5 | 8 | 1 | 0 | 0 |
| clinical research participant recruitment | balanced | 8 | 127 | 33 | 55 | 20 | 2 | 0 |
| clinical research participant recruitment | rich | 8 | 127 | 32 | 55 | 21 | 2 | 0 |
| climate change adaptation | focused | 3 | 37 | 8 | 12 | 1 | 0 | 0 |
| climate change adaptation | balanced | 8 | 127 | 31 | 55 | 21 | 1 | 0 |
| climate change adaptation | rich | 8 | 127 | 32 | 57 | 23 | 0 | 0 |
| hospital emergency department operations | focused | 8 | 127 | 36 | 60 | 22 | 0 | 0 |
| hospital emergency department operations | balanced | 8 | 127 | 32 | 62 | 28 | 2 | 0 |
| hospital emergency department operations | rich | 8 | 127 | 32 | 58 | 24 | 0 | 0 |
| software incident response | focused | 4 | 30 | 8 | 14 | 4 | 0 | 0 |
| software incident response | balanced | 8 | 127 | 31 | 54 | 21 | 4 | 0 |
| software incident response | rich | 8 | 127 | 31 | 51 | 17 | 3 | 0 |
| making a cup of tea | focused | 7 | 52 | 13 | 22 | 7 | 0 | 0 |
| making a cup of tea | balanced | 8 | 127 | 32 | 60 | 26 | 22 | 0 |
| making a cup of tea | rich | 8 | 127 | 32 | 61 | 27 | 11 | 0 |

The 127-node results are the existing internal node-budget boundary. Several
runs also recorded depth, relevance, marginal-value, or branch-pruning stops;
they did not represent a fixed profile depth.

## Representative trees

Focused clinical recruitment stopped at useful planning-level leaves:

```text
clinical research participant recruitment
└── Recruitment strategy and planning
    ├── Define target population and eligibility criteria
    ├── Select recruitment channels and methods
    ├── Develop recruitment materials and messaging
    └── Establish budget, timeline, and metrics for recruitment
```

Balanced clinical recruitment retained meaningful deeper branches, but also
reached implementation-heavy detail before safety limits, for example:

```text
Recruitment strategy and planning
└── Define target population and eligibility criteria
    └── Validate criteria against clinical and statistical requirements
        └── Translate clinical objectives into measurable criteria
            └── Deconstruct objectives into variables
```

Focused incident response preserved conceptual operational structure without
exhausting the graph budget:

```text
software incident response
└── Preparation and Readiness
    └── Implement Monitoring, Alerting, and Logging Infrastructure
        └── Instrument Services and Infrastructure for Telemetry
```

Rich incident response continued into more detailed schema and signal work:

```text
Incident Detection and Analysis
└── Ingest and Normalize Telemetry
    └── Configure telemetry sources and collectors
        └── Define incident-relevant signals and schemas
            └── Identify candidate signals from monitoring and observability sources
```

The terminal-prone tea topic exposed the clearest over-decomposition:

```text
making a cup of tea
└── Ingredients and Materials
    └── Tea Leaves Selection
        └── Choose Tea Type
            └── Assess flavor preferences
```

Balanced and rich tea runs did produce decomposition-terminal decisions (22 and
11 respectively), but focused tea produced none and still reached depth 7.

## Semantic review

Observed:

- Decomposition-terminal decisions occurred in plausible terminal/detail
  regions, especially the tea run and some incident-response branches.
- Meaningful conceptual depth was preserved: focused incident response reached
  depth 4, and focused clinical recruitment/climate adaptation retained useful
  high-level structure.
- Focused often stopped earlier than balanced/rich for clinical recruitment,
  climate adaptation, and incident response.
- The profile ordering was not monotonic across all concepts. Hospital
  emergency operations reached the node budget under every profile, and focused
  hospital operations expanded more vertical nodes than balanced/rich.
- No decomposition fallbacks occurred in the 15 completed runs. The initial
  `deepseek-v4-flash` probe returned malformed horizontal JSON before adaptive
  traversal; the matrix therefore used stable `deepseek-chat` consistently.
- There were obvious unnecessary decompositions. “Making a cup of tea” reached
  procedural detail under focused, and balanced/rich reached the node budget
  despite terminal decisions.
- There is at least one possible premature-stop risk: focused clinical and
  climate runs stopped at depth 3, although this run does not establish that
  the omitted branches contained valuable additional insight.

## Provider-call impact

Decomposition calls were batched and represented approximately 17–46% of total
calls in these runs. Examples: focused clinical used 1 evaluation call out of 8
total; balanced clinical used 20 out of 55; rich climate used 23 out of 57.
The extra calls were substantial once many nodes became eligible, but they were
bounded by the existing provider-call and node safety limits.

## Heuristic-only comparison

A real-provider heuristic-only matrix was not run. The repository has no clean
production baseline switch, and reproducing all 15 runs would roughly double
provider cost. The deterministic fallback path is covered by unit and
integration tests, but those tests do not establish a semantic-quality baseline
against real provider output.

## Findings and recommendations

The integration is functioning: calls are batched, decisions are applied by
candidate ID, terminal candidates remain in the graph, and fallback behavior
was not unexpectedly triggered. The evaluator provides useful terminal signals
in some balanced/rich runs, but this initial run does not demonstrate consistent
improvement in stopping behavior. Focused is not reliably more conservative,
and simple procedural topics can still over-decompose.

No tuning or architectural change is made in this validation phase. The next
evidence needed before changing prompts or thresholds is a controlled
heuristic-only comparison on a smaller fixed concept set, plus review of the
per-decision reasons for the tea and hospital cases.
