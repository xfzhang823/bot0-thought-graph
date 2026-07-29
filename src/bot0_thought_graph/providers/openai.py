"""OpenAI adapters; SDK-specific types remain inside this module."""

from typing import Any

from openai import AsyncOpenAI, OpenAI

from .contracts import (
    AsyncLLMProvider,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderRequestError,
    ProviderResponseError,
)


def _extract_text(response: Any) -> str:
    try:
        text = response.choices[0].message.content
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise ProviderResponseError("OpenAI response did not contain message text") from exc
    if not isinstance(text, str):
        raise ProviderResponseError("OpenAI response message text was not a string")
    return text


class OpenAIProvider(LLMProvider):
    """Synchronous OpenAI adapter with explicit or injected client construction."""

    provider_name = "openai"

    def __init__(self, client: OpenAI | None = None, *, api_key: str | None = None):
        if client is None:
            if not api_key:
                raise ValueError("api_key or an OpenAI client is required")
            client = OpenAI(api_key=api_key)
        self.client = client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if request.timeout is not None:
                kwargs["timeout"] = request.timeout
            response = self.client.chat.completions.create(**kwargs)
            return GenerationResult(_extract_text(response), self.provider_name, request.model)
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("OpenAI generation failed") from exc


class AsyncOpenAIProvider(AsyncLLMProvider):
    """Asynchronous OpenAI adapter with explicit or injected client construction."""

    provider_name = "openai"

    def __init__(self, client: AsyncOpenAI | None = None, *, api_key: str | None = None):
        if client is None:
            if not api_key:
                raise ValueError("api_key or an OpenAI client is required")
            client = AsyncOpenAI(api_key=api_key)
        self.client = client

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if request.timeout is not None:
                kwargs["timeout"] = request.timeout
            response = await self.client.chat.completions.create(**kwargs)
            return GenerationResult(_extract_text(response), self.provider_name, request.model)
        except ProviderResponseError:
            raise
        except Exception as exc:
            raise ProviderRequestError("OpenAI generation failed") from exc
