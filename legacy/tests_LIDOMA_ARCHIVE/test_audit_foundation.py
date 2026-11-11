from lidoma_engines.audit import AuditRecord


def test_audit_record_creation():

    record = AuditRecord(
        audit_id="audit.alpha",
        entity_id="decision.alpha",
        action="decision_created",
        details={
            "status": "success"
        },
    )

    assert record.audit_id == (
        "audit.alpha"
    )

    assert record.entity_id == (
        "decision.alpha"
    )

    assert record.details["status"] == (
        "success"
    )


def test_audit_validation():

    try:
        AuditRecord(
            audit_id="",
            entity_id="decision.alpha",
            action="created",
        )

        assert False

    except ValueError:
        assert True