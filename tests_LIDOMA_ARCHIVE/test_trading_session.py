from datetime import time

from lidoma_core.models.entities import (
    TradingSession,
    SessionType,
)


def test_trading_session_creation():

    session = TradingSession(
        name="London Session",
        session_type=SessionType.LONDON,
        timezone="Europe/London",
        open_time=time(8, 0),
        close_time=time(17, 0),
        active_days=(
            "MONDAY",
            "TUESDAY",
            "WEDNESDAY",
            "THURSDAY",
            "FRIDAY",
        ),
    )

    assert session.name == "London Session"
    assert session.session_type == SessionType.LONDON
    assert session.is_active_day("MONDAY") is True
    assert session.is_active_day("SATURDAY") is False


def test_trading_session_without_name():

    try:
        TradingSession(
            name="",
            session_type=SessionType.NEW_YORK,
            timezone="America/New_York",
            open_time=time(9, 30),
            close_time=time(16, 0),
            active_days=("MONDAY",),
        )

        assert False

    except ValueError:
        assert True