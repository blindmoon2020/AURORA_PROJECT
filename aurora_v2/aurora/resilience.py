"""Resilience: what the platform is allowed to do when the internet is not there.

Three states, and the platform must know which one it is in rather than discovering
it mid-decision:

  LIVE     fresh data this run; normal behaviour
  CACHED   the source is unreachable but a recent answer exists; decisions may be
           produced, stamped with the age of the data, and never silently presented
           as live
  OFFLINE  no usable data: no new positions, existing book marked against the last
           known prices, and the report says so

The rule that makes this safe is a hard staleness ceiling per interval. A cached
1d bar three days old is a degraded-but-usable input; a cached 1h bar three days
old is a lie about the present, and it is refused.
"""
from dataclasses import dataclass
from typing import Dict, Optional

LIVE, CACHED, OFFLINE = "live", "cached", "offline"

# hours of acceptable staleness per interval, deliberately tight
MAX_AGE_HOURS: Dict[str, float] = {
    "1m": 1.0, "5m": 4.0, "15m": 12.0, "30m": 24.0,
    "1h": 30.0, "4h": 72.0, "1d": 120.0, "1wk": 336.0, "1mo": 1200.0,
}


@dataclass(frozen=True)
class DataState:
    mode: str
    interval: str
    age_hours: Optional[float]
    reason: str = ""

    @property
    def usable(self) -> bool:
        return self.mode in (LIVE, CACHED)

    @property
    def may_open_positions(self) -> bool:
        """New risk requires live data. Managing what exists does not."""
        return self.mode == LIVE

    def stamp(self) -> str:
        if self.mode == LIVE:
            return "live"
        if self.mode == CACHED:
            return f"cached {self.age_hours:.1f}h old"
        return f"offline: {self.reason}"


def assess(interval: str, age_hours: Optional[float], fetch_failed: bool) -> DataState:
    """Decide the state from two facts: did the fetch fail, and how old is the cache."""
    if not fetch_failed and age_hours is not None and age_hours <= MAX_AGE_HOURS.get(interval, 24.0):
        return DataState(LIVE, interval, age_hours)
    if fetch_failed and age_hours is None:
        return DataState(OFFLINE, interval, None, "no cache and no connection")
    limit = MAX_AGE_HOURS.get(interval, 24.0)
    if age_hours is not None and age_hours <= limit:
        return DataState(CACHED, interval, age_hours, "source unreachable, cache within limit")
    return DataState(OFFLINE, interval, age_hours,
                     f"cache {age_hours:.0f}h old exceeds {limit:.0f}h limit for {interval}")
