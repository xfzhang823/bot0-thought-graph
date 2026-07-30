"""Thin coordination facade for application callers."""

from bot0_thought_graph.interview import InterviewContext, InterviewEngine, InterviewSession, InterviewTurnResult


class InterviewCoordinator:
    """Delegate interview operations without adding I/O or persistence behavior."""

    def __init__(self, engine: InterviewEngine) -> None:
        self.engine = engine

    def start(self, context: InterviewContext) -> InterviewSession:
        return self.engine.start(context)

    def process_answer(self, session: InterviewSession, answer: str) -> InterviewTurnResult:
        return self.engine.process_answer(session, answer)

    def save_session(self, session: InterviewSession) -> None:
        self.engine.save_session(session)
