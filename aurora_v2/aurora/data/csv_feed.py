"""CSV adapter. The escape hatch for real data: export from MT5, TradingView,
a broker statement, anywhere. Column names are matched case-insensitively and
the first row must be a header.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Sequence

from ..core.types import Candle

COLUMN_ALIASES = {
    "ts": ("ts", "time", "date", "datetime", "timestamp"),
    "open": ("open", "o"),
    "high": ("high", "h"),
    "low": ("low", "l"),
    "close": ("close", "c", "last"),
    "volume": ("volume", "vol", "v", "tickvol"),
}


class CsvFeedError(ValueError):
    pass


def _resolve(header: Sequence[str]) -> dict:
    lowered = {h.strip().lower(): i for i, h in enumerate(header)}
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lowered:
                mapping[field] = lowered[alias]
                break
    required = ("ts", "open", "high", "low", "close")
    missing = [f for f in required if f not in mapping]
    if missing:
        raise CsvFeedError(f"csv is missing columns {missing}; found header {list(header)}")
    return mapping


def _parse_ts(value: str) -> int:
    text = value.strip()
    if text.isdigit():
        return int(text)
    try:
        from datetime import datetime, timezone

        text = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError as exc:
        raise CsvFeedError(f"unparseable timestamp {value!r}") from exc


def load_csv(path: str | Path) -> List[Candle]:
    p = Path(path)
    if not p.exists():
        raise CsvFeedError(f"csv not found: {p}")
    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise CsvFeedError(f"{p}: empty file") from exc
        cols = _resolve(header)
        out: List[Candle] = []
        for lineno, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue
            try:
                out.append(
                    Candle(
                        ts=_parse_ts(row[cols["ts"]]),
                        open=float(row[cols["open"]]),
                        high=float(row[cols["high"]]),
                        low=float(row[cols["low"]]),
                        close=float(row[cols["close"]]),
                        volume=float(row[cols["volume"]]) if "volume" in cols and row[cols["volume"]] else 0.0,
                    )
                )
            except (ValueError, IndexError) as exc:
                raise CsvFeedError(f"{p}: bad row {lineno}: {exc}") from exc
    if not out:
        raise CsvFeedError(f"{p}: no candles parsed")
    return out


def write_csv(candles: Iterable[Candle], path: str | Path) -> Path:
    p = Path(path)
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "open", "high", "low", "close", "volume"])
        for c in candles:
            writer.writerow([c.ts, c.open, c.high, c.low, c.close, c.volume])
    return p
