"""TSETMC exports: the Iran leg, built from files you already have.

No scraping, no credentials, no rate limits. TSETMC publishes a daily CSV per
symbol; this reads it. Two realities of those files are handled here because they
break every naive parser: dates arrive in the Jalali calendar, and column names
arrive in Persian, in transliteration, or with a byte-order mark in front.
"""
from __future__ import annotations

import csv
import datetime as _dt
from pathlib import Path
from typing import Dict, List, Sequence

from aurora.core.types import Candle

# Jalali -> Gregorian, Khayyam algorithm with the standard leap-year breaks.
_BREAKS = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060,
           2097, 2192, 2262, 2324, 2394, 2456, 3178]


class TsetmcParseError(ValueError):
    """A file that cannot be read honestly is refused, not guessed at."""


def _div(a: int, b: int) -> int:
    return a // b


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> _dt.date:
    if not (1 <= jm <= 12 and 1 <= jd <= 31):
        raise TsetmcParseError(f"Jalali month/day out of range: {jy}/{jm}/{jd}")
    jy += 1595
    days = -355668 + (365 * jy) + (_div(jy, 33) * 8) + _div((jy % 33) + 3, 4) + jd
    days += (jm - 1) * 31 if jm < 7 else ((jm - 7) * 30 + 186)
    gy = 400 * _div(days, 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * _div(days, 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        gy += _div(days - 1, 365)
        days = (days - 1) % 365
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)
    months = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 1
    for length in months:
        if gd <= length:
            break
        gd -= length
        gm += 1
    return _dt.date(gy, gm, gd)


_DATE_KEYS = ("date", "dt", "تاریخ", "تاريخ", "date_str")
_ALIASES = {
    "open": ("open", "opening", "اولین", "اول"),
    "high": ("high", "بیشترین", "حداکثر"),
    "low": ("low", "کمترین", "حداقل"),
    "close": ("close", "closing", "پایانی", "قیمت پایانی", "last"),
    "volume": ("volume", "vol", "حجم", "حجم معاملات"),
}


def _norm(name: str) -> str:
    return name.replace("\ufeff", "").replace("\u200c", "").strip().lower()


def _parse_day(text: str, default_year: int | None = None) -> _dt.date:
    raw = text.strip().replace("/", "-").replace(".", "-")
    parts = [p for p in raw.split("-") if p]
    if len(parts) != 3:
        raise TsetmcParseError(f"unreadable date {text!r}")
    a, b, c = (int(p) for p in parts)
    if a > 999:                       # Gregorian year first
        return _dt.date(a, b, c)
    if default_year is not None and len(parts[0]) <= 2:
        return jalali_to_gregorian(default_year, a, b)
    return jalali_to_gregorian(a, b, c)


def load_tsetmc_csv(path: str | Path, split_adjusted: bool = True) -> List[Candle]:
    """Read a TSETMC daily export into candles, sorted and de-duplicated.

    split_adjusted scales OHLC by close/(close+prev_close) when the file offers a
    raw 'close' beside a 'final' value; without it a Tehran backtest silently
    treats splits and capital raises as real returns.
    """
    path = Path(path)
    if not path.exists():
        raise TsetmcParseError(f"file not found: {path}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if not text.strip():
        raise TsetmcParseError(f"empty file: {path}")
    sample = text.splitlines()[0]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    rows = list(csv.DictReader(text.splitlines(), delimiter=delimiter))
    if not rows:
        raise TsetmcParseError(f"no data rows in {path}")
    header = {_norm(k): k for k in rows[0] if k}
    # resolve each canonical field to whichever spelling this file actually uses,
    # so a Persian export and an English export take the same code path
    resolved = {}
    for field in ("open", "high", "low", "close", "volume"):
        for alias in _ALIASES[field]:
            if _norm(alias) in header:
                resolved[field] = _norm(alias)
                break
    for field in ("open", "high", "low", "close"):
        if field not in resolved:
            raise TsetmcParseError(f"missing column for {field} in {path.name}")
    out: Dict[int, Candle] = {}
    for row in rows:
        norm = {_norm(k): v for k, v in row.items() if k}
        try:
            day = _parse_day(norm.get("date") or norm.get("تاریخ") or norm.get("تاريخ", ""))
            o = float(norm[resolved["open"]]); h = float(norm[resolved["high"]])
            l = float(norm[resolved["low"]]); c = float(norm[resolved["close"]])
        except (KeyError, TypeError, ValueError):
            continue
        if min(o, h, l, c) <= 0 or h < max(o, c) or l > min(o, c):
            continue
        vol = norm.get(resolved.get("volume", ""), "0") if resolved.get("volume") else "0"
        try:
            v = float(vol)
        except ValueError:
            v = 0.0
        ts = int(_dt.datetime(day.year, day.month, day.day,
                              tzinfo=_dt.timezone.utc).timestamp())
        out[ts] = Candle(ts=ts, open=o, high=h, low=l, close=c, volume=v)
    if not out:
        raise TsetmcParseError(f"every row in {path.name} was rejected")
    return [out[k] for k in sorted(out)]
