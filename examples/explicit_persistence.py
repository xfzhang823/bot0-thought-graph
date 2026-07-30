"""Demonstrate explicit, temporary JSON persistence without source-tree output."""

from tempfile import TemporaryDirectory

from support import FakeProvider, graph

from bot0_thought_graph import InterviewEngine, JsonRepository


provider = FakeProvider(["What are the key requirements?"])
with TemporaryDirectory() as directory:
    engine = InterviewEngine(
        provider,
        model="example-model",
        repository=JsonRepository(directory),
    )
    session = engine.start(graph())
    engine.save_session(session)
    print(f"Saved explicitly to the caller-selected temporary directory: {directory}")
