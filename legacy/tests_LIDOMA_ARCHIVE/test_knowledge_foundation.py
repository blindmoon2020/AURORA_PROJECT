from lidoma_engines.knowledge import KnowledgeRecord


def test_knowledge_record_creation():

    record = KnowledgeRecord(
        knowledge_id="knowledge.alpha",
        source_decision_id="decision.alpha",
        pattern="high_confidence_success",
        metadata={
            "score": 0.95
        },
    )

    assert record.knowledge_id == (
        "knowledge.alpha"
    )

    assert record.source_decision_id == (
        "decision.alpha"
    )

    assert record.metadata["score"] == 0.95


def test_knowledge_validation():

    try:
        KnowledgeRecord(
            knowledge_id="",
            source_decision_id="decision.alpha",
            pattern="pattern",
        )

        assert False

    except ValueError:
        assert True