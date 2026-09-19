from lidoma_engines import (
    ObservabilityRecord,
    HealthStatus,
)


def test_observability_health_flow():

    metric = ObservabilityRecord(
        metric_id="metric.health.alpha",
        component="runtime",
        metric_type="availability",
        value=True,
    )

    health = HealthStatus(
        component=metric.component,
        healthy=True,
        checks={
            metric.metric_type: True
        },
    )

    assert health.component == (
        "runtime"
    )

    assert health.checks["availability"] is True


def test_health_timestamp_is_timezone_aware():

    health = HealthStatus(
        component="system",
        healthy=True,
    )

    assert health.created_at.tzinfo is not None