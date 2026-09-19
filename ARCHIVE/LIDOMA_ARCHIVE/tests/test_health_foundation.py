from lidoma_engines.health import HealthStatus


def test_health_status_creation():

    status = HealthStatus(
        component="decision_engine",
        healthy=True,
        checks={
            "database": True,
            "runtime": True,
        },
    )

    assert status.component == (
        "decision_engine"
    )

    assert status.healthy is True

    assert status.checks["database"] is True

    assert status.created_at.tzinfo is not None


def test_health_validation():

    try:
        HealthStatus(
            component="",
            healthy=True,
        )

        assert False

    except ValueError:
        assert True