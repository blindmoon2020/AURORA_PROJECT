"""Fundamental freshness: a number is only as true as the day it became public.

The point-in-time selector already refuses future filings. What it does not say is
how old the filing being used is, and that silence is dangerous in a different way:
a company that stopped filing two years ago still returns a value, sized and ranked
as if it were current. The ranking then treats silence as agreement.

So freshness is computed, reported, and in the extreme, refused:
  - every decision records the median filing age of the names it ranks
  - a name whose latest public filing is older than STALE_DAYS is flagged, and its
    fundamental weight is reduced to zero rather than using a number that stopped
    being true without anyone noticing
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence

STALE_DAYS = 550.0      # a full year plus a quarter of grace: annual plus a late filing
DAY = 86400.0


def _ts(day: str) -> int:
    return int(datetime.strptime(str(day)[:10], "%Y-%m-%d")
               .replace(tzinfo=timezone.utc).timestamp())


def public_at(rows: Sequence[dict], as_of_ts: int, date_field: str = "filing_date") -> Optional[dict]:
    """Most recent row already public at as_of_ts. Future rows never qualify."""
    eligible = [r for r in rows if str(r.get(date_field, "")) and _ts(r[date_field]) <= as_of_ts]
    if not eligible:
        return None
    return max(eligible, key=lambda r: r[date_field])


def age_days(row: dict, as_of_ts: int, date_field: str = "filing_date") -> float:
    return (as_of_ts - _ts(row[date_field])) / DAY


def is_stale(row: Optional[dict], as_of_ts: int, limit_days: float = STALE_DAYS) -> bool:
    if row is None:
        return True
    return age_days(row, as_of_ts) > limit_days


def guard_no_lookahead(rows: Iterable[dict], as_of_ts: int,
                       date_field: str = "filing_date") -> None:
    """Raise if anything handed to a decision was not public at decision time."""
    seen: List[str] = []
    for r in rows:
        day = str(r.get(date_field, ""))
        if not day:
            raise ValueError("filing without a publication date: cannot be used point-in-time")
        if _ts(day) > as_of_ts:
            seen.append(day)
    if seen:
        raise ValueError(f"{len(seen)} filing(s) not yet public at the decision: {sorted(seen)[:3]}")


@dataclass(frozen=True)
class Freshness:
    symbols: int
    median_age_days: float
    stale: List[str]

    def summary(self) -> str:
        base = f"{self.symbols} names, median filing age {self.median_age_days:.0f} days"
        if self.stale:
            return base + f", stale: {', '.join(self.stale[:6])}" + (
                "" if len(self.stale) <= 6 else f" (+{len(self.stale) - 6})")
        return base


def freshness(filings: Dict[str, Sequence[dict]], as_of_ts: int,
              limit_days: float = STALE_DAYS) -> Freshness:
    ages: List[float] = []
    stale: List[str] = []
    for sym, rows in filings.items():
        row = public_at(rows, as_of_ts)
        if row is None:
            stale.append(sym)
            continue
        ages.append(age_days(row, as_of_ts))
        if is_stale(row, as_of_ts, limit_days):
            stale.append(sym)
    return Freshness(len(filings), median(ages) if ages else float("nan"), sorted(stale))
