import importlib

import pytest


def load_behavior_test(monkeypatch, value=None):
    if value is None:
        monkeypatch.delenv("DEEPSEEK_THINKING", raising=False)
    else:
        monkeypatch.setenv("DEEPSEEK_THINKING", value)
    return importlib.import_module("examples.behavior_test")


@pytest.mark.parametrize(
    ("value", "expected"), [("enabled", True), ("disabled", False)]
)
def test_parse_deepseek_thinking(value, expected, monkeypatch):
    behavior_test = load_behavior_test(monkeypatch, value)
    assert behavior_test.parse_deepseek_thinking() is expected


def test_parse_deepseek_thinking_absent_uses_provider_default(monkeypatch):
    behavior_test = load_behavior_test(monkeypatch)
    assert behavior_test.parse_deepseek_thinking() is None


def test_parse_deepseek_thinking_rejects_invalid_value(monkeypatch):
    behavior_test = load_behavior_test(monkeypatch, "maybe")
    with pytest.raises(ValueError, match="Use 'enabled' or 'disabled'"):
        behavior_test.parse_deepseek_thinking()
