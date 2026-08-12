"""Behavioral harness for the public thought-generation API.

Example:
    ```bash
    python examples/behavior_test.py \
        --topic "clinical research participant recruitment" \
        --provider deepseek \
        --model deepseek-v4-flash \
        --depth 2 \
        --breadth 5 \
        --progression implementation_steps
    ```

The script prints the selected configuration and a readable tree view of the
generated thought graph.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

from bot0_thought_graph import ProgressionType, ThoughtGraphEngine

DEFAULT_TOPIC = "clinical research participant recruitment"
DEFAULT_PROVIDER = "openai"
DEFAULT_DEPTH = 2
DEFAULT_BREADTH = 5
DEFAULT_PROGRESSION = ProgressionType.IMPLEMENTATION_STEPS


@dataclass(frozen=True)
class RuntimeConfig:
    topic: str
    provider: str
    model: str | None
    depth: int
    breadth: int
    progression_type: ProgressionType


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
        choices=["openai", "gemini", "deepseek", "anthropic"],
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
        "--depth",
        type=int,
        default=int(_env_default("BEHAVIOR_TEST_DEPTH", str(DEFAULT_DEPTH))),
        help="Number of vertical expansion levels to generate.",
    )
    parser.add_argument(
        "--breadth",
        type=int,
        default=int(_env_default("BEHAVIOR_TEST_BREADTH", str(DEFAULT_BREADTH))),
        help="Number of children retained per expanded node.",
    )
    parser.add_argument(
        "--progression",
        default=_env_default("BEHAVIOR_TEST_PROGRESSION", DEFAULT_PROGRESSION.value),
        choices=[item.value for item in ProgressionType],
        help="Vertical progression type for graph expansion.",
    )
    return parser


def resolve_config(argv: list[str] | None = None) -> RuntimeConfig:
    args = build_parser().parse_args(argv)
    return RuntimeConfig(
        topic=args.topic,
        provider=args.provider,
        model=args.model,
        depth=args.depth,
        breadth=args.breadth,
        progression_type=ProgressionType(args.progression),
    )


def print_header(config: RuntimeConfig, resolved_model: str) -> None:
    print("Thought Graph Behavioral Test")
    print("=============================")
    print()
    print(f"Topic:        {config.topic}")
    print(f"Provider:     {config.provider}")
    print(f"Model:        {resolved_model}")
    print(f"Depth:        {config.depth}")
    print(f"Breadth:      {config.breadth}")
    print(f"Progression:  {config.progression_type.value}")
    print()


def print_tree(node, *, prefix: str = "", is_last: bool = True, is_root: bool = False) -> None:
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


def main(argv: list[str] | None = None) -> None:
    """Run one public thought-graph generation and print it.

    Example:
        ```bash
        python examples/behavior_test.py --help
        ```
    """
    config = resolve_config(argv)
    engine = ThoughtGraphEngine(provider=config.provider, model=config.model)
    graph = engine.generate_thought_graph(
        topic=config.topic,
        depth=config.depth,
        breadth=config.breadth,
        progression_type=config.progression_type,
    )

    print_header(config, engine.model)
    print_tree(graph.root, is_root=True)


if __name__ == "__main__":
    main()
