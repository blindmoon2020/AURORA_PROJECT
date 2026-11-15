"""When is a venue actually open? Checked before an order, not after a rejection.

The gap this closes: AURORA knew each venue's hours as text in the catalogue, but nothing
consulted them at decision time, so a target could be built for a market that was shut. The
check uses the venue's own timezone via zoneinfo, so daylight saving is handled by the tz
database rather than by an offset someone guessed once.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from aurora.core import asset_universe as au

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

RANGES = {
    "Mon-Fri": {0, 1, 2, 3, 4},
    "Sat-Wed": {5, 6, 0, 1, 2},
    "Mon-Sat": {0, 1, 2, 3, 4, 5},
    "Sun-Thu": {6, 0, 1, 2, 3},
    "24/7": {0, 1, 2, 3, 4, 5, 6},
}


def _days(days: str) -> set:
    if days in RANGES:
        return RANGES[days]
    if days in WEEKDAYS:                     # a single named day
        return {WEEKDAYS.index(days)}
    raise ValueError(f"روزهای هفته ناشناخته: {days}")


def _minutes(hhmm: str) -> int:
    hour, minute = hhmm.split(":")
    return int(hour) * 60 + int(minute)


def is_venue_open(venue_code: str, at_utc: datetime) -> Tuple[bool, str]:
    """Returns (open, reason). An unknown venue is closed with a reason, never assumed open."""
    try:
        v = au.venue(venue_code)
    except Exception:
        return False, f"بورس {venue_code} در کاتالوگ نیست؛ وضعیت نامعلوم است"

    if at_utc.tzinfo is None:
        at_utc = at_utc.replace(tzinfo=timezone.utc)
    if v.days == "24/7":
        return True, f"{v.name}: بازار ۲۴/۷ باز است"

    local = at_utc.astimezone(__import__("zoneinfo").ZoneInfo(v.timezone))
    if local.weekday() not in _days(v.days):
        return False, f"{v.name}: {WEEKDAYS[local.weekday()]} تعطیل است ({v.days})"

    now_min = local.hour * 60 + local.minute
    open_min, close_min = _minutes(v.open_local), _minutes(v.close_local)
    spans_midnight = close_min <= open_min
    inside = (now_min >= open_min or now_min < close_min) if spans_midnight \
        else (open_min <= now_min < close_min)
    if not inside:
        return False, (f"{v.name}: خارج از ساعت معاملات "
                       f"({v.open_local}-{v.close_local} به وقت {v.timezone})")
    return True, f"{v.name}: باز ({v.open_local}-{v.close_local} به وقت {v.timezone})"


def gate(symbol: str, at_utc: datetime) -> Tuple[bool, str]:
    """Order-level gate: is this instrument's venue open right now?"""
    try:
        inst = au.get(symbol)
    except Exception:
        return False, f"{symbol} در کاتالوگ نیست؛ بازار و ساعتش نامعلوم است"
    return is_venue_open(inst.venue, at_utc)
