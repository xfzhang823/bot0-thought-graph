"""Provider-injected, in-memory interview engine."""

from typing import Any

from bot0_thought_graph.models import IdeaJSONModel, IndexedIdeaJSONModel
from bot0_thought_graph.providers import LLMProvider
from bot0_thought_graph.storage import Repository
from bot0_thought_graph.thought_generation import index_idea

from .evaluation import EvaluationService
from .models import InterviewContext, InterviewSession, InterviewTurn, InterviewTurnResult
from .question_generation import QuestionGenerationService
from .reflection import ReflectionService
from .state import has_current_sub_thought, next_location
from .topic_exhaustion import TopicExhaustionPolicy


class InterviewEngine:
    """Coordinate interview services without I/O, SDK construction, or implicit saves."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        model: str,
        thought_engine: Any | None = None,
        repository: Repository[Any] | None = None,
        question_service: QuestionGenerationService | None = None,
        evaluation_service: EvaluationService | None = None,
        reflection_service: ReflectionService | None = None,
        exhaustion_policy: TopicExhaustionPolicy | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.thought_engine = thought_engine
        self.repository = repository
        self.question_service = question_service or QuestionGenerationService(provider, model=model)
        self.evaluation_service = evaluation_service or EvaluationService(provider, model=model)
        self.reflection_service = reflection_service or ReflectionService()
        self.exhaustion_policy = exhaustion_policy or TopicExhaustionPolicy()

    def start(self, context: InterviewContext | IndexedIdeaJSONModel | IdeaJSONModel) -> InterviewSession:
        if isinstance(context, IdeaJSONModel):
            context = InterviewContext(idea_data=index_idea(context))
        elif isinstance(context, IndexedIdeaJSONModel):
            context = InterviewContext(idea_data=context)
        if not has_current_sub_thought(context.idea_data, 0, 0):
            raise ValueError("Interview context contains no sub-thoughts")
        sub_thought = context.idea_data.thoughts[0].sub_thoughts[0]
        question = self.question_service.initial(
            topic_name=sub_thought.name,
            context_text=sub_thought.description,
        )
        return InterviewSession(
            context=context,
            current_question=question,
            asked_questions=[question],
        )

    def process_answer(self, session: InterviewSession, answer: str) -> InterviewTurnResult:
        if session.status == "completed":
            raise ValueError("Interview session is already completed")
        if not session.current_question:
            raise ValueError("Interview session has no current question")
        graph = session.context.idea_data
        thought = graph.thoughts[session.thought_index]
        sub_thought = (thought.sub_thoughts or [])[session.sub_thought_index]
        evaluation = self.evaluation_service.evaluate(
            question=session.current_question,
            answer=answer,
            idea=graph.idea,
            thought=thought.thought,
        )
        session.turns.append(
            InterviewTurn(
                question=session.current_question,
                answer=answer,
                evaluation=evaluation,
                thought_index=session.thought_index,
                sub_thought_index=session.sub_thought_index,
            )
        )
        session.current_evaluation = evaluation
        session.evaluations.append(evaluation)
        session.session_metadata.total_interactions += 1
        logs = [{"role": "agent", "message": turn.question} for turn in session.turns]
        logs.extend({"role": "user", "message": turn.answer} for turn in session.turns)
        self.exhaustion_policy.set_scoped_logs(logs)
        exhaustion = self.exhaustion_policy.evaluate(answer)
        session.exhaustion_state = exhaustion
        location = next_location(graph, session.thought_index, session.sub_thought_index)
        decision = self.reflection_service.decide(evaluation, has_next_topic=location is not None)
        if exhaustion["is_exhausted"] and location is not None:
            decision = decision.model_copy(update={"action": "advance", "reason": "Topic exhaustion threshold reached."})
        if decision.action in {"advance", "complete"}:
            if location is None:
                session.status = "completed"
                session.current_question = None
                return InterviewTurnResult(
                    session=session,
                    evaluation=evaluation,
                    completed=True,
                    topic_exhausted=bool(exhaustion["is_exhausted"]),
                    decision="complete",
                    decision_reason=decision.reason,
                )
            session.thought_index, session.sub_thought_index = location
            next_sub_thought = graph.thoughts[location[0]].sub_thoughts[location[1]]
            next_question = self.question_service.initial(
                topic_name=next_sub_thought.name,
                context_text=next_sub_thought.description,
                asked_questions=session.asked_questions,
            )
        else:
            next_question = self.question_service.follow_up(
                evaluation=evaluation,
                idea=graph.idea,
                thought=thought.thought,
                sub_thought_description=sub_thought.description,
                context_logs=logs,
                asked_questions=session.asked_questions,
            )
        session.current_question = next_question
        session.asked_questions.append(next_question)
        return InterviewTurnResult(
            session=session,
            evaluation=evaluation,
            next_question=next_question,
            topic_exhausted=bool(exhaustion["is_exhausted"]),
            decision=decision.action,
            decision_reason=decision.reason,
        )

    def save_session(self, session: InterviewSession) -> None:
        if self.repository is None:
            raise RuntimeError("No repository was supplied; sessions remain in memory")
        self.repository.save(session.session_id, session.model_dump())
