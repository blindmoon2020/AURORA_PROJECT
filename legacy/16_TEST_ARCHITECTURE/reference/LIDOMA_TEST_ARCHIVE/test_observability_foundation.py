from lidoma_engines.observability import ObservabilityRecord


def test_observability_record_creation():

    record = ObservabilityRecord(
        metric_id="metric.alpha",
        component="decision_engine",
        metric_type="latency",
        value=120,
        metadata={
            "unit": "ms"
        },
    )

    assert record.metric_id == (
        "metric.alpha"
    )

    assert record.component == (
        "decision_engine"
    )

    assert record.value == 120


def test_observability_validation():

    try:
        ObservabilityRecord(
            metric_id="",
            component="engine",
            metric_type="latency",
            value=10,
        )

        assert False

    except ValueError:
        assert True