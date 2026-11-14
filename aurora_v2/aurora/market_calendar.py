"""Market calendar: a decision fills at the next real open, and only that one.

Two failures this prevents, both of which quietly corrupt cost calibration:

1. Filling at the open of a bar three weeks later. That difference is not slippage,
   it is the market moving while nothing happened. Measuring it as execution cost
   inflates the cost estimate with drift and the strategy looks worse than it is.
2. Counting a session that produced nothing. A run on a closed market is not a
   session, and counting it inflates the sample size of every later statistic.

Holidays are enumerated rather than guessed: an exchange holiday that the code does
not know about turns into a phantom session, so the list is explicit and dated.
"""
import datetime as _dt
from typing import Optional
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
OPEN_HOUR, OPEN_MIN = 9, 30
CLOSE_HOUR, CLOSE_MIN = 16, 0

# US equity full-day closures. Half days are handled as normal sessions with an
# early close note; they do not affect the fill rule.
HOLIDAYS = {
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
    "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
}


def _et(ts: float) -> _dt.datetime:
    return _dt.datetime.fromtimestamp(ts, tz=ET)


def is_trading_day(day: _dt.date | str) -> bool:
    if isinstance(day, str):
        day = _dt.date.fromisoformat(day)
    if day.weekday() >= 5:          # Saturday, Sunday
        return False
    return day.isoformat() not in HOLIDAYS


def is_open(ts: float) -> bool:
    """Is the regular session open at this instant?"""
    now = _et(ts)
    if not is_trading_day(now.date()):
        return False
    minutes = now.hour * 60 + now.minute
    return OPEN_HOUR * 60 + OPEN_MIN <= minutes < CLOSE_HOUR * 60 + CLOSE_MIN


def open_of(day: _dt.date) -> float:
    return _dt.datetime(day.year, day.month, day.day, OPEN_HOUR, OPEN_MIN,
                        tzinfo=ET).timestamp()


def next_session_open(ts: float) -> float:
    """The first regular open strictly after this instant."""
    day = _et(ts).date()
    for _ in range(14):
        day = day + _dt.timedelta(days=1)
        if is_trading_day(day):
            return open_of(day)
    raise ValueError("no trading day within two weeks: calendar is stale")


def session_open_on_or_after(ts: float) -> float:
    """Used to check whether a bar really is the next open after a decision."""
    day = _et(ts).date()
    candidate = day if is_trading_day(day) else None
    while candidate is None:
        day = day + _dt.timedelta(days=1)
        if is_trading_day(day):
            candidate = day
    return open_of(candidate)


def fill_is_next_open(decided_ts: float, fill_ts: float, tolerance_hours: float = 6.0) -> bool:
    """True when the fill timestamp is the open of the first session after the decision.

    Tolerance absorbs the difference between the exchange open and the timestamp the
    bar carries, without admitting a fill that skipped a session.
    """
    expected = next_session_open(decided_ts)
    return abs(fill_ts - expected) <= tolerance_hours * 3600.0
