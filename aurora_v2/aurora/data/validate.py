"""Data hygiene before a single number is trusted.

A backtest is only as good as the bars under it. This reports what is wrong
with the series instead of quietly averaging over it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.types import Candle


@dataclass
class DataReport:
    rows: int
    duplicates: int = 0
    out_of_order: int = 0
    zero_range: int = 0
    gaps: List[Tuple[int, int, int]] = field(default_factory=list)  # (index, ts, bars_missing)
    missing_bars: int = 0
    expected_bars: int = 0
    coverage_pct: float = 100.0
    extreme_returns: int = 0
    first_ts: int = 0
    last_ts: int = 0
    median_bar_seconds: int = 0
    issues: Dict[str, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return not self.duplicates and not self.out_of_order and self.zero_range == 0 \
            and self.coverage_pct >= 99.0 and self.extreme_returns == 0

    def report(self) -> str:
        lines = [
            f"rows={self.rows} first={self.first_ts} last={self.last_ts} "
            f"median_bar={self.median_bar_seconds}s",
            f"coverage={self.coverage_pct:.2f}% missing_bars={self.missing_bars} "
            f"gaps={len(self.gaps)}",
            f"duplicates={self.duplicates} out_of_order={self.out_of_order} "
            f"zero_range={self.zero_range} extreme_returns={self.extreme_returns}",
        ]
        if self.gaps[:3]:
            lines.append(f"largest gaps (index, ts, bars_missing): {self.gaps[:3]}")
        if self.issues:
            lines.append(f"issues: {self.issues}")
        return "\n".join(lines)


def _is_market_closed(ts: int, profile: str) -> bool:
    """FX closes Friday evening to Sunday evening UTC; 24/7 for crypto profile."""
    if profile != "fx":
        return False
    from datetime import datetime, timezone

    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    wd, hour = dt.weekday(), dt.hour  # Monday=0
    if wd == 5:
        return True
    if wd == 4 and hour >= 21:
        return True
    if wd == 6 and hour < 21:
        return True
    return False


OHLC_TOLERANCE = 0.005   # 50bp: repair a print glitch, never hide a 5% error


def _repair(c: Candle) -> Optional[Candle]:
    """Keep a bar whose close sits a hair outside high/low by widening the range.

    Both Twelve Data and Yahoo ship such prints. Dropping them is worse than the
    glitch itself: one bad tick upstream should not delete a whole instrument.
    """
    hi, lo, close = c.high, c.low, c.close
    if hi < lo:
        hi, lo = lo, hi
    if lo <= close <= hi:
        if (hi, lo) == (c.high, c.low):
            return c
        return Candle(ts=c.ts, open=c.open, high=hi, low=lo, close=c.close,
                      volume=getattr(c, "volume", 0.0))
    ref = max(abs(hi), abs(lo), 1e-12)
    if abs(close - (hi if close > hi else lo)) / ref <= OHLC_TOLERANCE:
        return Candle(ts=c.ts, open=c.open, high=max(hi, close), low=min(lo, close),
                      close=c.close, volume=getattr(c, "volume", 0.0))
    return None


def clean_candles(
    candles: Sequence[Candle], profile: str = "fx"
) -> tuple[List[Candle], DataReport]:
    """Sort, deduplicate, drop zero-range bars, and report what was removed."""
    report = DataReport(rows=len(candles))
    if not candles:
        report.issues["empty"] = "no candles"
        return [], report

    ordered = sorted(candles, key=lambda c: c.ts)
    cleaned: List[Candle] = []
    seen = set()
    last_ts = None
    for c in ordered:
        if c.ts in seen:
            report.duplicates += 1
            continue
        if last_ts is not None and c.ts < last_ts:
            report.out_of_order += 1
        if c.high == c.low:
            report.zero_range += 1
            continue
        fixed = _repair(c)
        if fixed is None:
            report.issues.setdefault("ohlc_inconsistent", 0)
            report.issues["ohlc_inconsistent"] += 1
            continue
        cleaned.append(fixed)
        seen.add(c.ts)
        last_ts = c.ts

    if len(cleaned) < 2:
        report.issues["too_short"] = "fewer than two usable bars"
        report.rows = len(cleaned)
        return cleaned, report

    report.rows = len(cleaned)
    report.first_ts, report.last_ts = cleaned[0].ts, cleaned[-1].ts
    deltas = sorted(b.ts - a.ts for a, b in zip(cleaned, cleaned[1:]) if b.ts > a.ts)
    bar = int(median(deltas)) if deltas else 0
    report.median_bar_seconds = bar

    if bar > 0:
        # A gap only counts when the market should have been open: FX weekends
        # are closed, and calling them missing data would be a lie about quality.
        for i in range(1, len(cleaned)):
            gap = cleaned[i].ts - cleaned[i - 1].ts
            missing_ts = range(cleaned[i - 1].ts + bar, cleaned[i].ts, bar)
            missing = sum(1 for t in missing_ts if not _is_market_closed(t, profile))
            if missing > 0:
                report.gaps.append((i, cleaned[i].ts, int(missing)))
                report.missing_bars += int(missing)
        expected = sum(
            1 for t in range(cleaned[0].ts, cleaned[-1].ts + bar, bar)
            if not _is_market_closed(t, profile)
        )
        report.expected_bars = int(expected)
        report.coverage_pct = len(cleaned) / expected * 100 if expected else 0.0
        report.gaps.sort(key=lambda g: -g[2])

    closes = [c.close for c in cleaned]
    rets = [(b / a - 1.0) for a, b in zip(closes, closes[1:]) if a > 0]
    if rets:
        mad = median([abs(r) for r in rets])
        if mad > 0:
            report.extreme_returns = sum(1 for r in rets if abs(r) > 50 * mad)

    if report.coverage_pct < 95:
        report.issues["coverage"] = f"only {report.coverage_pct:.1f}% of expected bars present"
    if report.duplicates:
        report.issues["duplicates"] = f"{report.duplicates} duplicate timestamps"
    if report.extreme_returns:
        report.issues["outliers"] = f"{report.extreme_returns} returns beyond 50x median absolute return"
    return cleaned, report
