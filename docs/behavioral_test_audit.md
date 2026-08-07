# Behavioral Test Audit

Date: 2026-08-07

Git branch: `main`

Git commit hash: `36914401aed44291ddad31652a99e1870848ed28`

Provider implementation: `OpenAIProvider` from `src/bot0_thought_graph/providers/openai.py`

Selected model: `gpt-5-mini-2025-08-07`

Relevant API/configuration path:

`OPENAI_API_KEY` -> `bot0_thought_graph._env.load_repository_env()` -> `bot0_thought_graph.providers.build_sync_client()` -> `OpenAIProvider()` -> `ThoughtGraphEngine(provider, model=MODEL)` -> `generate_array_of_thoughts(...)` / `expand_subtopic(...)`

Test concept: `Clinical research recruitment`

Methods being tested:

- `ThoughtGraphEngine.generate_array_of_thoughts("Clinical research recruitment", max_subtopics=6)`
- `ThoughtGraphEngine.expand_subtopic(concept="Clinical research recruitment", subtopic=<selected>, max_details=6)`

Behavioral expectations:

Horizontal behavior:

- sibling consistency
- distinctness
- coverage
- concept relevance
- granularity consistency

Vertical direct-child behavior:

- parent-child relationship
- specificity
- scope control
- distinctness
- granularity consistency

Scoring rubric:

- 0 = failure
- 1 = partially satisfactory
- 2 = satisfactory

Targets:

- Horizontal: `>= 8/10`
- Vertical: `>= 8/10`

Failure categories to track:

- mixed abstraction levels
- sibling overlap
- horizontal item is actually a task
- vertical child belongs to another branch
- parent repeated as child
- near-duplicate thoughts
- concept drift
- missing major dimension
- uneven granularity

Raw horizontal output:

<!-- populate after live run -->

Horizontal score:

<!-- populate after live run -->

Horizontal failure observations:

<!-- populate after live run -->

Selected vertical parent:

<!-- populate after live run -->

Raw vertical output:

<!-- populate after live run -->

Vertical score:

<!-- populate after live run -->

Vertical failure observations:

<!-- populate after live run -->

Overall conclusion:

<!-- populate after live run -->

Follow-up action:

<!-- populate after live run -->
