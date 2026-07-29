import json
from types import SimpleNamespace

import pytest

from bot0_thought_graph.config import Bot0Config, ProviderConfig
from bot0_thought_graph.providers import (
    AnthropicProvider,
    AsyncAnthropicProvider,
    AsyncOpenAIProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    OpenAIProvider,
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
    completions = FakeCompletions(SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]))
    provider = OpenAIProvider(client=SimpleNamespace(chat=SimpleNamespace(completions=completions)))
    assert isinstance(provider, LLMProvider)
    result = provider.generate(request())
    assert isinstance(result, GenerationResult)
    assert result.text == "answer"
    assert completions.calls[0]["timeout"] == 4


def test_anthropic_adapter_and_malformed_responses():
    messages = FakeMessages(SimpleNamespace(content=[SimpleNamespace(text="answer")]))
    provider = AnthropicProvider(client=SimpleNamespace(messages=messages))
    assert provider.generate(request()).text == "answer"

    malformed = AnthropicProvider(
        client=SimpleNamespace(messages=FakeMessages(SimpleNamespace(content=[])))
    )
    with pytest.raises(ProviderResponseError):
        malformed.generate(request())


def test_provider_exception_translation_and_no_import_time_clients():
    failing_openai = OpenAIProvider(
        client=SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(error=RuntimeError("offline"))))
    )
    with pytest.raises(ProviderRequestError):
        failing_openai.generate(request())
    with pytest.raises(ValueError):
        OpenAIProvider()
    with pytest.raises(ValueError):
        AnthropicProvider()


@pytest.mark.asyncio
async def test_async_adapters_use_injected_clients():
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
