"""Run offline horizontal thought generation."""

from support import FakeProvider

from bot0_thought_graph import ThoughtGraphEngine
from bot0_thought_graph.thought_generation import HorizontalGenerationRequest


provider = FakeProvider(
    ['{"idea":"systems","thoughts":[{"thought":"hardware","description":"Physical design"}]}']
)
engine = ThoughtGraphEngine(provider)
result = engine.generate(HorizontalGenerationRequest(idea="systems", model="example-model"))
print(result.model_dump_json(indent=2))
