# Prompts

This package owns graph-generation prompt templates as public, overridable
constants.

## Responsibilities

- `thought_generation_prompt_templates.py`: horizontal, vertical, and
  concept/detail generation prompts.
- `evaluation_prompt_templates.py`: retained question/answer evaluation and
  follow-up templates, plus related evaluation exports. These are compatibility
  surfaces and are not interview orchestration; the graph engine's ranking
  prompt is `RECLUSTER_AND_PICK_TOP_CLUSTER_PROMPT`.
- `__init__.py`: the stable prompt-constant exports.

Prompt templates define the provider-facing instructions and response shapes;
the engine supplies runtime concepts, progression, and model settings.

## Boundaries

Prompts do not invoke providers, parse responses, construct graph nodes, or
implement traversal/reflection policy. Graph generation consumes the horizontal,
vertical, and ranking templates; retained evaluation/question constants are not
used to provide interview/application orchestration here.
