import json
import os
from types import SimpleNamespace

import pytest

from bot0_thought_graph import _env as env_module
from bot0_thought_graph.config import Bot0Config, ProviderConfig
from bot0_thought_graph.providers import (
    create_provider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderRequestError,
    ProviderResponseError,
)
from bot0_thought_graph.storage import JsonRepository, MemoryRepository


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def request():
    return GenerationRequest("Explain systems", "test-model", timeout=4)


def test_provider_contract_and_openai_adapter_without_network():
    OpenAIProvider = pytest.importorskip("bot0_thought_graph.providers.openai").OpenAIProvider
    completions = FakeCompletions(SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]))
    provider = OpenAIProvider(client=SimpleNamespace(chat=SimpleNamespace(completions=completions)))
    assert isinstance(provider, LLMProvider)
    result = provider.generate(request())
    assert isinstance(result, GenerationResult)
    assert result.text == "answer"
    assert completions.calls[0]["timeout"] == 4


def test_anthropic_adapter_and_malformed_responses():
    AnthropicProvider = pytest.importorskip("bot0_thought_graph.providers.anthropic").AnthropicProvider
    messages = FakeMessages(SimpleNamespace(content=[SimpleNamespace(text="answer")]))
    provider = AnthropicProvider(client=SimpleNamespace(messages=messages))
    assert provider.generate(request()).text == "answer"

    malformed = AnthropicProvider(
        client=SimpleNamespace(messages=FakeMessages(SimpleNamespace(content=[])))
    )
    with pytest.raises(ProviderResponseError):
        malformed.generate(request())


def test_provider_exception_translation_and_no_import_time_clients(monkeypatch, tmp_path):
    OpenAIProvider = pytest.importorskip("bot0_thought_graph.providers.openai").OpenAIProvider
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")
    failing_openai = OpenAIProvider(
        client=SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(error=RuntimeError("offline"))))
    )
    with pytest.raises(ProviderRequestError):
        failing_openai.generate(request())
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    monkeypatch.setattr(helper_module, "load_repository_env", lambda: None)
    with pytest.raises(ValueError):
        OpenAIProvider()


def test_repository_env_loader_respects_os_precedence(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=dotenv-openai\nANTHROPIC_API_KEY=dotenv-anthropic\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "os-openai")

    monkeypatch.setattr(env_module, "_find_env_file", lambda filename: env_file)
    env_module.load_repository_env()

    assert os.environ["OPENAI_API_KEY"] == "os-openai"
    assert os.environ["ANTHROPIC_API_KEY"] == "dotenv-anthropic"


def test_openai_provider_uses_openai_api_key_from_environment(monkeypatch):
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "os-openai")
    monkeypatch.setattr(helper_module, "load_repository_env", lambda: None)

    seen = {}

    class FakeOpenAI:
        def __init__(self, api_key):
            seen["api_key"] = api_key
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(helper_module, "OpenAI", FakeOpenAI)
    pytest.importorskip("bot0_thought_graph.providers.openai").OpenAIProvider()
    assert seen["api_key"] == "os-openai"


def test_anthropic_provider_uses_anthropic_api_key_from_environment(monkeypatch):
    anthropic_module = pytest.importorskip("bot0_thought_graph.providers.anthropic")

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "os-anthropic")

    seen = {}

    class FakeAnthropic:
        def __init__(self, api_key):
            seen["api_key"] = api_key
            self.messages = SimpleNamespace(create=lambda **kwargs: None)

    monkeypatch.setattr(anthropic_module, "Anthropic", FakeAnthropic)
    anthropic_module.AnthropicProvider()
    assert seen["api_key"] == "os-anthropic"


def test_gemini_provider_uses_openai_compatible_base_url_and_api_key(monkeypatch):
    gemini_module = pytest.importorskip("bot0_thought_graph.providers.gemini")
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "os-gemini")
    monkeypatch.setattr(helper_module, "load_repository_env", lambda: None)

    seen = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.chat = SimpleNamespace(
                completions=FakeCompletions(
                    SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="gemini-answer"))]
                    )
                )
            )

    monkeypatch.setattr(helper_module, "OpenAI", FakeOpenAI)
    provider = gemini_module.GeminiProvider()
    result = provider.generate(request())

    assert seen["api_key"] == "os-gemini"
    assert seen["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert provider.client.chat.completions.calls[0]["messages"] == [
        {"role": "user", "content": "Explain systems"}
    ]
    assert provider.client.chat.completions.calls[0]["model"] == "test-model"
    assert result.text == "gemini-answer"


def test_deepseek_provider_uses_openai_compatible_base_url_and_reasoning_separation(monkeypatch):
    deepseek_module = pytest.importorskip("bot0_thought_graph.providers.deepseek")
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "os-deepseek")
    monkeypatch.setattr(helper_module, "load_repository_env", lambda: None)

    seen = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)
            self.chat = SimpleNamespace(
                completions=FakeCompletions(
                    SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content="final answer",
                                    reasoning_content="hidden reasoning",
                                )
                            )
                        ]
                    )
                )
            )

    monkeypatch.setattr(helper_module, "OpenAI", FakeOpenAI)
    provider = deepseek_module.DeepSeekProvider()
    result = provider.generate(request())

    assert seen["api_key"] == "os-deepseek"
    assert seen["base_url"] == "https://api.deepseek.com"
    assert provider.client.chat.completions.calls[0]["messages"] == [
        {"role": "user", "content": "Explain systems"}
    ]
    assert provider.client.chat.completions.calls[0]["model"] == "test-model"
    assert result.text == "final answer"
    assert result.reasoning_content == "hidden reasoning"


def test_provider_factory_supports_gemini_and_deepseek(monkeypatch):
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")
    monkeypatch.setattr(helper_module, "load_repository_env", lambda: None)
    monkeypatch.setenv("GEMINI_API_KEY", "os-gemini")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "os-deepseek")

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.chat = SimpleNamespace(
                completions=FakeCompletions(
                    SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))])
                )
            )

    monkeypatch.setattr(helper_module, "OpenAI", FakeOpenAI)
    assert create_provider("gemini").provider_name == "gemini"
    assert create_provider("deepseek").provider_name == "deepseek"


def test_openai_compatible_requests_use_completion_token_field_for_gpt5_models():
    helper_module = pytest.importorskip("bot0_thought_graph.providers.openai_compatible")
    request = GenerationRequest("Explain systems", "gpt-5-mini-2025-08-07", max_tokens=42)
    kwargs = helper_module.build_chat_completion_kwargs(request)
    assert "temperature" not in kwargs
    assert "max_tokens" not in kwargs
    assert kwargs["reasoning_effort"] == "minimal"
    assert kwargs["max_completion_tokens"] == 42


@pytest.mark.asyncio
async def test_async_adapters_use_injected_clients():
    AsyncOpenAIProvider = pytest.importorskip("bot0_thought_graph.providers.openai").AsyncOpenAIProvider
    AsyncAnthropicProvider = pytest.importorskip("bot0_thought_graph.providers.anthropic").AsyncAnthropicProvider
    class AsyncCompletions(FakeCompletions):
        async def create(self, **kwargs):
            return super().create(**kwargs)

    class AsyncMessages(FakeMessages):
        async def create(self, **kwargs):
            return super().create(**kwargs)

    openai_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=AsyncCompletions(
                SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="openai"))])
            )
        )
    )
    anthropic_client = SimpleNamespace(
        messages=AsyncMessages(SimpleNamespace(content=[SimpleNamespace(text="anthropic")]))
    )
    assert (await AsyncOpenAIProvider(client=openai_client).generate(request())).text == "openai"
    assert (await AsyncAnthropicProvider(client=anthropic_client).generate(request())).text == "anthropic"


def test_memory_repository_is_ephemeral_and_copying():
    repository = MemoryRepository()
    value = {"items": [1]}
    repository.save("session", value)
    value["items"].append(2)
    assert repository.load("session") == {"items": [1]}
    with pytest.raises(KeyError):
        repository.load("missing")


def test_json_repository_round_trip_invalid_json_and_explicit_path(tmp_path):
    repository = JsonRepository(tmp_path / "chosen" / "data")
    repository.save("thoughts", {"b": 2, "a": [1]})
    assert repository.load("thoughts") == {"a": [1], "b": 2}
    assert json.loads((tmp_path / "chosen" / "data" / "thoughts.json").read_text()) == {"a": [1], "b": 2}
    with pytest.raises(FileNotFoundError):
        repository.load("missing")
    (tmp_path / "chosen" / "data" / "bad.json").write_text("not json")
    with pytest.raises(json.JSONDecodeError):
        repository.load("bad")
    with pytest.raises(ValueError):
        repository.save("../escape", {})


def test_configuration_is_explicit_and_has_no_storage_default():
    config = Bot0Config(provider=ProviderConfig(provider="openai", model="test-model"))
    assert config.provider.model == "test-model"
    assert not hasattr(config, "storage_path")
