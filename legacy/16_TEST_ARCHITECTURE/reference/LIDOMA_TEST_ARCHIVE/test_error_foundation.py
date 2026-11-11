from datetime import datetime

import pytest

from lidoma_engines.errors import LIDOMAErrorRecord


def test_error_record_creation():

    error = LIDOMAErrorRecord(
        error_id="error.alpha",
        component="decision_engine",
        error_type="validation_error",
        message="invalid decision state",
    )

    assert error.error_id == "error.alpha"
    assert error.component == "decision_engine"
    assert error.error_type == "validation_error"
    assert error.message == "invalid decision state"

    assert error.created_at.tzinfo is not None
    assert error.created_at.utcoffset() is not None


def test_error_rejects_empty_error_id():

    with pytest.raises(ValueError):

        LIDOMAErrorRecord(
            error_id="",
            component="engine",
            error_type="failure",
            message="error",
        )


def test_error_rejects_empty_component():

    with pytest.raises(ValueError):

        LIDOMAErrorRecord(
            error_id="error.alpha",
            component="",
            error_type="failure",
            message="error",
        )


def test_error_rejects_empty_error_type():

    with pytest.raises(ValueError):

        LIDOMAErrorRecord(
            error_id="error.alpha",
            component="engine",
            error_type="",
            message="error",
        )


def test_error_rejects_empty_message():

    with pytest.raises(ValueError):

        LIDOMAErrorRecord(
            error_id="error.alpha",
            component="engine",
            error_type="failure",
            message="",
        )


def test_error_rejects_naive_created_at():

    with pytest.raises(ValueError):

        LIDOMAErrorRecord(
            error_id="error.alpha",
            component="engine",
            error_type="failure",
            message="error",
            created_at=datetime.now(),
        )


def test_error_instances_receive_independent_timestamps():

    first = LIDOMAErrorRecord(
        error_id="error.first",
        component="engine",
        error_type="failure",
        message="first",
    )

    second = LIDOMAErrorRecord(
        error_id="error.second",
        component="engine",
        error_type="failure",
        message="second",
    )

    assert first.created_at is not second.created_at