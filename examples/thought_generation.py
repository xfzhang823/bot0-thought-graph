"""Run the concept-first thought-generation workflow offline."""

import json

from support import FakeProvider

from bot0_thought_graph import ThoughtGraphEngine


HORIZONTAL = (
    '{"idea":"systems","thoughts":['
    '{"thought":"hardware","description":"Physical design"},'
    '{"thought":"software","description":"Program logic"}]}'
)
VERTICAL = (
    '{"idea":"systems","thought":"hardware","sub_thoughts":['
    '{"name":"requirements","description":"Define needs"},'
    '{"name":"design","description":"Choose structure"}]}'
)


# The fake provider makes this example deterministic and network-free.
provider = FakeProvider([HORIZONTAL, VERTICAL, HORIZONTAL, HORIZONTAL, VERTICAL, VERTICAL])
engine = ThoughtGraphEngine(provider, model="example-model")

subtopics = engine.generate_subtopics("systems", max_subtopics=2)
details = engine.expand_subtopic("systems", "hardware", max_details=2)
thought_array = engine.generate_array_of_thoughts("systems", max_subtopics=2)
graph = engine.generate_thought_graph("systems", depth=2, breadth=2)

print("subtopics:", subtopics)
print("details:", details)
print("thought_array:")
print(thought_array.model_dump_json(indent=2))
print("thought_graph:")
print(json.dumps(graph.model_dump(), indent=2))
