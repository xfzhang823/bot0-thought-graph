from agents.state_transition_machine import ConversationMetrics, TopicExhaustionService


def test_legacy_topic_exhaustion_service_remains_self_contained():
    service = TopicExhaustionService()
    service.set_scoped_logs([{"role": "user", "message": "same answer"}])

    result = service.is_topic_exhausted("same answer")

    assert isinstance(service.metrics, ConversationMetrics)
    assert set(result) == {"is_exhausted", "redundancy_score", "new_info_score"}
