import ast
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "bot0_thought_graph"


def test_public_top_level_api_is_small_and_importable():
    namespace = {}
    exec("from bot0_thought_graph import *", namespace)
    assert {
        "ThoughtGraphEngine",
        "InterviewEngine",
        "InterviewCoordinator",
        "LLMProvider",
        "AsyncLLMProvider",
        "MemoryRepository",
        "JsonRepository",
    } <= namespace.keys()
    assert "extract_json" not in namespace


def test_package_has_no_legacy_or_platform_path_dependencies():
    forbidden = ("C:/github/", "src/C:/", "input_output", "find_project_root", "project_config")
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden), path
        tree = ast.parse(text)
        assert not any(
            isinstance(node, ast.Import) and any(alias.name == "sys" for alias in node.names)
            for node in ast.walk(tree)
        ), path


def test_import_works_outside_repository_without_sdk_adapter_imports(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import bot0_thought_graph; import bot0_thought_graph.providers; print('ok')",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "ok"


def test_provider_package_does_not_construct_or_import_adapters_at_import_time(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    code = (
        "import sys; import bot0_thought_graph.providers; "
        "assert 'bot0_thought_graph.providers.openai' not in sys.modules; "
        "assert 'bot0_thought_graph.providers.anthropic' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, check=True)
