"""Provider-neutral contracts with lazy SDK adapter exports."""

from importlib import import_module

from .contracts import (
    AsyncLLMProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderError,
    ProviderRequestError,
    ProviderResponseError,
)

_LAZY_ADAPTERS = {
    "AnthropicProvider": (".anthropic", "AnthropicProvider"),
    "AsyncAnthropicProvider": (".anthropic", "AsyncAnthropicProvider"),
    "AsyncOpenAIProvider": (".openai", "AsyncOpenAIProvider"),
    "OpenAIProvider": (".openai", "OpenAIProvider"),
}


def __getattr__(name: str):
    if name not in _LAZY_ADAPTERS:
        raise AttributeError(name)
    module_name, attribute = _LAZY_ADAPTERS[name]
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value

__all__ = [
    "AnthropicProvider", "AsyncAnthropicProvider", "AsyncLLMProvider",
    "AsyncOpenAIProvider", "GenerationRequest", "GenerationResult", "LLMProvider",
    "OpenAIProvider", "ProviderError", "ProviderRequestError", "ProviderResponseError",
]
