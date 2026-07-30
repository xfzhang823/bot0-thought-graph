"""Run one offline interview turn."""

from support import FakeProvider, graph

from bot0_thought_graph import InterviewEngine


provider = FakeProvider(
    [
        "What are the key requirements?",
        '{"evaluation":{"criteria":{"relevance":5,"correctness":5,"specificity":4,"clarity":5},"explanations":{"relevance":"Direct.","correctness":"Correct.","specificity":"Specific.","clarity":"Clear."},"total_score":4.75}}',
    ]
)
engine = InterviewEngine(provider, model="example-model")
session = engine.start(graph())
turn = engine.process_answer(session, "Requirements define system needs.")
print(turn.model_dump_json(indent=2))
