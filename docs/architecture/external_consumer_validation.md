# External Consumer Validation

Validation was performed against the built distributions, from temporary
environments outside the repository and without adding the repository to
`PYTHONPATH`.

## Artifacts

- Wheel: `dist/bot0_thought_graph-0.1.0-py3-none-any.whl`
- Source distribution: `dist/bot0_thought_graph-0.1.0.tar.gz`

The wheel contains the canonical `bot0_thought_graph` package with its
`thought_generation`, `reflection`, `providers`, `models`, `prompts`, and
`storage` packages, plus `public_api.py` and `config.py`. It contains no
`interview`, `orchestration`, `agents`, `pipelines`, or unqualified legacy
top-level package directories. The sdist contains the corresponding `src/`
package tree and build metadata.

Wheel metadata declares the package's runtime dependencies only. It contains
no runtime `pytest`, `pytest-asyncio`, or `aiohttp` dependency. Development
dependencies remain available only through the `dev` extra/dependency group.

## Clean wheel environment

A fresh Python 3.12 virtual environment was created at
`/tmp/bot0-external-validation.vOYBv6/venv` and installed from the wheel with
its declared runtime dependencies. The installed import origin was:

```text
/tmp/bot0-external-validation.vOYBv6/venv/lib/python3.12/site-packages/bot0_thought_graph/__init__.py
```

Root imports succeeded without requiring credentials or making a provider
request:

```python
from bot0_thought_graph import generate_thought_graph, ThoughtGraphEngine
from bot0_thought_graph.models import ProgressionType, Thought, ThoughtArray, ThoughtGraph, ThoughtNode
from bot0_thought_graph.providers import AsyncLLMProvider, LLMProvider
from bot0_thought_graph.storage import MemoryRepository
```

The retired imports `bot0_thought_graph.interview` and
`bot0_thought_graph.orchestration` failed as expected.

## Injected-provider validation

An external consumer script used a small provider implementing the existing
`LLMProvider` contract. It called:

```python
graph = generate_thought_graph(
    "coffee brewing methods",
    exploration="balanced",
    provider=fake_provider,
    model="external-test-model",
)
```

The script ran from the temporary directory, returned `ThoughtGraph`, produced
the expected root/child content, and made two canonical generation calls.
`ThoughtGraphEngine` was also importable from the installed distribution.

## Named-provider configuration

Named provider factory resolution worked for OpenAI and Anthropic using
injected clients. The existing `OPENAI_MODEL` environment override resolved
through `default_model("openai")`. Missing-credential behavior was verified
against the configured external environment; a credential was present, so the
provider could be constructed. No provider defaults or configuration behavior
were changed.

## Real-provider smoke test

One minimal OpenAI request was run from the wheel-installed environment for
`coffee brewing methods` with `exploration="focused"`. The request succeeded
and returned a `ThoughtGraph` containing generated child content. Credentials
and environment values were not printed.

## Sdist validation

The sdist was installed into a second fresh Python 3.12 environment at
`/tmp/bot0-sdist-validation.GyEycF/venv`. It rebuilt and installed
successfully. Its import origin was:

```text
/tmp/bot0-sdist-validation.GyEycF/venv/lib/python3.12/site-packages/bot0_thought_graph/__init__.py
```

Root imports, `ThoughtGraphEngine`, the convenience function, and retired
namespace absence all passed.

## Conclusion

The built wheel and sdist are usable from a separate consumer environment. The
root convenience API, advanced engine API, canonical models/providers/storage,
retired namespace boundaries, and injected-provider generation path all work
without repository-local imports. No packaging or public-API defect was found,
and no production code was changed during this validation.
