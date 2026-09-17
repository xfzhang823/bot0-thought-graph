import os
import subprocess
import sys
from pathlib import Path

from bot0_thought_graph.reflection import (
    DecompositionEvaluationService,
)


ROOT = Path(__file__).resolve().parents[1]


def test_core_reflection_owns_decomposition():
    assert DecompositionEvaluationService.__module__ == (
        "bot0_thought_graph.reflection.decomposition"
    )


def test_root_graph_import_does_not_eagerly_load_interview():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    code = """
import sys
import bot0_thought_graph

assert not any(
    name == "bot0_thought_graph.interview"
    or name.startswith("bot0_thought_graph.interview.")
    for name in sys.modules
)
"""
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def test_interview_namespace_is_not_available():
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib.util; assert importlib.util.find_spec('bot0_thought_graph.interview') is None",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def test_thought_generation_has_no_interview_reflection_import():
    thought_generation = ROOT / "src" / "bot0_thought_graph" / "thought_generation"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in thought_generation.rglob("*.py")
    )
    assert "bot0_thought_graph.interview.reflection" not in source
    assert "bot0_thought_graph.reflection" in source
