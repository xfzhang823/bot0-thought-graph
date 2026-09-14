"""Behavioral harness for the public thought-generation API.

Examples:

    Adaptive exploration (default: balanced):

        python examples/behavior_test.py \
            --topic "clinical research participant recruitment" \
            --provider deepseek \
            --model deepseek-v4-flash

    Explicit graph bounds:

        python examples/behavior_test.py \
            --topic "clinical research participant recruitment" \
            --provider openai \
            --horizontal 2 \
            --vertical 6 \
            --progression implementation_steps

    Legacy compatibility mode:

        python examples/behavior_test.py \
                --topic "clinical research participant recruitment" \
                --provider openai \
                --breadth 5 \
                --depth 2

    Persist the generated graph explicitly:

        python examples/behavior_test_adaptive.py \
            --provider openai \
            --topic "participant recruitment for a post-stroke gait rehabilitation study using a wearable robotic
            exoskeleton" \
            --exploration balanced \
            --insert ./examples/output \
            --insert-key recruitment-graph

    This persists the graph to ``./output/recruitment-graph.json``. Replace
    ``./output`` with any directory where you want to keep the result.

The script prints the selected configuration, the generated tree, and adaptive
exploration diagnostics when adaptive mode is used. When ``--insert`` is
provided, it also persists the generated graph as JSON.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from support import FakeProvider

from bot0_thought_graph import JsonRepository, ProgressionType, ThoughtGraphEngine

DEFAULT_TOPIC = "participant recruitment for a post-stroke gait rehabilitation study using a wearable robotic exoskeleton"
DEFAULT_PROVIDER = "openai"
DEFAULT_EXPLORATION = "balanced"
DEFAULT_PROGRESSION = ProgressionType.IMPLEMENTATION_STEPS


@dataclass(frozen=True)
class RuntimeConfig:
    topic: str
    provider: str
    model: str | None
    mode: str
    exploration: str | None
    horizontal: int | None
    vertical: int | None
    depth: int | None
    breadth: int | None
    progression_type: ProgressionType
    insert_directory: str | None
    insert_key: str


def _env_default(name: str, fallback: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else fallback


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a public thought-graph behavior check with one graph output."
    )
    parser.add_argument(
        "--topic",
        default=_env_default("BEHAVIOR_TEST_TOPIC", DEFAULT_TOPIC),
        help="Root topic to expand.",
    )
    parser.add_argument(
        "--provider",
        default=_env_default("THOUGHT_GRAPH_PROVIDER", DEFAULT_PROVIDER),
        choices=["openai", "gemini", "deepseek", "anthropic", "fake"],
        help="LLM provider to use.",
    )
    parser.add_argument(
        "--model",
        default=_env_optional("THOUGHT_GRAPH_MODEL"),
        help=(
            "Optional provider model override. When omitted, the provider's "
            "default model is used."
        ),
    )
    parser.add_argument(
        "--exploration",
        choices=["focused", "balanced", "rich"],
        default=_env_optional("BEHAVIOR_TEST_EXPLORATION"),
        help="Adaptive exploration profile. Defaults to balanced when no explicit graph-shape controls are supplied.",
    )
    parser.add_argument(
        "--horizontal",
        type=int,
        default=None,
        help="Explicit mode: maximum root-level peer directions.",
    )
    parser.add_argument(
        "--vertical",
        type=int,
        default=None,
        help="Explicit mode: maximum generated child levels beneath the root.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Legacy compatibility mode: graph depth.",
    )
    parser.add_argument(
        "--breadth",
        type=int,
        default=None,
        help="Legacy compatibility mode: breadth retained per expanded node.",
    )
    parser.add_argument(
        "--progression",
        default=_env_default("BEHAVIOR_TEST_PROGRESSION", DEFAULT_PROGRESSION.value),
        choices=[item.value for item in ProgressionType],
        help="Vertical progression type for graph expansion.",
    )
    parser.add_argument(
        "--insert",
        dest="insert_directory",
        default=_env_optional("BEHAVIOR_TEST_INSERT_DIR"),
        help=(
            "Persist the generated graph as JSON in this directory. "
            "Persistence is opt-in."
        ),
    )
    parser.add_argument(
        "--insert-key",
        default=_env_default("BEHAVIOR_TEST_INSERT_KEY", "generated-graph"),
        help="Filename stem used with --insert (default: generated-graph).",
    )
    return parser


def resolve_config(argv: list[str] | None = None) -> RuntimeConfig:
    parser = build_parser()
    args = parser.parse_args(argv)

    has_explicit = args.horizontal is not None or args.vertical is not None
    has_legacy = args.breadth is not None or args.depth is not None

    if has_explicit and has_legacy:
        parser.error("Do not mix horizontal/vertical with legacy breadth/depth.")

    if has_explicit:
        if args.exploration is not None:
            parser.error("Do not mix --exploration with --horizontal/--vertical.")
        if args.horizontal is None or args.vertical is None:
            parser.error("Explicit mode requires both --horizontal and --vertical.")
        mode = "explicit"
        exploration = None
    elif has_legacy:
        if args.exploration is not None:
            parser.error("Do not mix --exploration with --breadth/--depth.")
        if args.breadth is None or args.depth is None:
            parser.error("Legacy mode requires both --breadth and --depth.")
        mode = "legacy"
        exploration = None
    else:
        mode = "adaptive"
        exploration = args.exploration or DEFAULT_EXPLORATION

    return RuntimeConfig(
        topic=args.topic,
        provider=args.provider,
        model=args.model,
        mode=mode,
        exploration=exploration,
        horizontal=args.horizontal,
        vertical=args.vertical,
        depth=args.depth,
        breadth=args.breadth,
        progression_type=ProgressionType(args.progression),
        insert_directory=args.insert_directory,
        insert_key=args.insert_key,
    )


def _fake_response_sequence(config: RuntimeConfig) -> list[str]:
    """Build deterministic fake responses for explicit/legacy smoke testing."""
    if config.mode == "adaptive":
        raise ValueError(
            "Use a real provider to behavior-test adaptive exploration; "
            "the fake provider is reserved for explicit/legacy smoke tests."
        )

    if config.mode == "explicit":
        assert config.horizontal is not None
        assert config.vertical is not None
        root_count = config.horizontal
        depth = config.vertical
        vertical_children = 7
    else:
        assert config.breadth is not None
        assert config.depth is not None
        root_count = config.breadth
        depth = config.depth
        vertical_children = config.breadth

    horizontal = {
        "idea": config.topic,
        "thoughts": [
            {
                "thought": f"subtopic-{index + 1}",
                "description": f"Auto-generated subtopic {index + 1}",
            }
            for index in range(root_count)
        ],
    }

    vertical = {
        "idea": config.topic,
        "thought": "subtopic-1",
        "sub_thoughts": [
            {
                "name": f"detail-{index + 1}",
                "description": f"Auto-generated detail {index + 1}",
            }
            for index in range(vertical_children)
        ],
    }

    vertical_calls = 0
    nodes_at_level = root_count
    for _ in range(1, depth):
        vertical_calls += nodes_at_level
        nodes_at_level *= vertical_children

    return [json.dumps(horizontal)] + [json.dumps(vertical)] * vertical_calls


def build_provider(config: RuntimeConfig):
    if config.provider == "fake":
        return FakeProvider(_fake_response_sequence(config))
    return config.provider


def print_header(config: RuntimeConfig, resolved_model: str) -> None:
    print("Thought Graph Behavioral Test")
    print("=============================")
    print()
    print(f"Topic:        {config.topic}")
    print(f"Provider:     {config.provider}")
    print(f"Model:        {resolved_model}")
    print(f"Mode:         {config.mode}")
    if config.mode == "adaptive":
        print(f"Exploration:  {config.exploration}")
    elif config.mode == "explicit":
        print(f"Horizontal:   {config.horizontal}")
        print(f"Vertical:     {config.vertical}")
    else:
        print(f"Depth:        {config.depth}")
        print(f"Breadth:      {config.breadth}")
    print(f"Progression:  {config.progression_type.value}")
    print()


def print_tree(
    node, *, prefix: str = "", is_last: bool = True, is_root: bool = False
) -> None:
    if is_root:
        print(node.name)
        if node.description:
            for line in node.description.splitlines():
                print(f"    {line}")
        child_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{node.name}")
        if node.description:
            description_prefix = f"{prefix}{'    ' if is_last else '│   '}"
            for line in node.description.splitlines():
                print(f"{description_prefix}{line}")
        child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
    for index, child in enumerate(node.children):
        print_tree(child, prefix=child_prefix, is_last=index == len(node.children) - 1)


def _trace_value(item, name: str, fallback: str = "") -> str:
    if isinstance(item, dict):
        value = item.get(name, fallback)
    else:
        value = getattr(item, name, fallback)
    if hasattr(value, "value"):
        value = value.value
    return "" if value is None else str(value)


def print_exploration_trace(engine: ThoughtGraphEngine) -> None:
    trace = getattr(engine, "last_exploration_trace", None)
    profile = getattr(engine, "last_exploration_profile", None)

    print()
    print("Exploration Trace")
    print("=================")
    print(f"Profile: {profile or 'unknown'}")

    if not trace:
        print("(no trace entries)")
        return

    for index, item in enumerate(trace, start=1):
        axis = _trace_value(item, "axis", "?")
        action = _trace_value(item, "action", "?")
        reason = _trace_value(item, "reason", "?")
        level = _trace_value(item, "level", "?")
        thought = _trace_value(item, "thought")
        suffix = f" | {thought}" if thought else ""
        print(
            f"{index:>3}. level={level} axis={axis} "
            f"action={action} reason={reason}{suffix}"
        )


def main(argv: list[str] | None = None) -> None:
    """Run one public thought-graph generation and print it.

    Example:
        ```bash
        python examples/behavior_test.py --help
        ```
    """
    config = resolve_config(argv)
    engine = ThoughtGraphEngine(
        provider=build_provider(config),
        # Let named providers resolve their package default model when the
        # CLI does not supply --model. The fake provider does not need a
        # provider-specific model.
        model=config.model,
        repository=(
            JsonRepository(config.insert_directory) if config.insert_directory else None
        ),
    )
    common = {
        "topic": config.topic,
        "progression_type": config.progression_type,
    }

    if config.mode == "adaptive":
        graph = engine.generate_thought_graph(
            **common,
            exploration=config.exploration,
        )
    elif config.mode == "explicit":
        graph = engine.generate_thought_graph(
            **common,
            horizontal=config.horizontal,
            vertical=config.vertical,
        )
    else:
        graph = engine.generate_thought_graph(
            **common,
            depth=config.depth,
            breadth=config.breadth,
        )

    print_header(config, engine.model)
    print_tree(graph.root, is_root=True)

    if config.insert_directory:
        engine.save(config.insert_key, graph)
        print(
            f"\nPersisted graph to "
            f"{config.insert_directory.rstrip('/')}/{config.insert_key}.json"
        )

    if config.mode == "adaptive":
        print_exploration_trace(engine)


if __name__ == "__main__":
    main()
