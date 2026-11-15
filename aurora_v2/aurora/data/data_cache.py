"""A local candle cache so the platform is fast and survives a cut connection.

QuantConnect and Aladdin both keep bars locally; AURORA fetched from the network on every
run. This is the smallest useful version: SQLite (stdlib, no server), one row per
(symbol, timeframe, timestamp), so a repeated fetch is a no-op and an offline run can still
read yesterday's data and say how old it is.
"""
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

SCHEMA = """
CREATE TABLE IF NOT EXISTS candles (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    ts INTEGER NOT NULL,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    PRIMARY KEY (symbol, timeframe, ts)
);
CREATE INDEX IF NOT EXISTS idx_candles_lookup ON candles (symbol, timeframe, ts DESC);
"""


@dataclass(frozen=True)
class CacheStats:
    rows: int
    symbols: int
    newest_ts: Optional[int]

    def line(self) -> str:
        return f"{self.rows} کندل · {self.symbols} نماد · جدیدترین: {self.newest_ts or '—'}"


class CandleCache:
    def __init__(self, path: str | Path = "data_cache/candles.db"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def put(self, symbol: str, timeframe: str, candles: Sequence) -> int:
        """Insert bars, ignoring ones already stored. Returns how many were new."""
        rows = [(symbol, timeframe, int(c.ts), float(c.open), float(c.high), float(c.low),
                 float(c.close), float(getattr(c, "volume", 0.0) or 0.0)) for c in candles]
        if not rows:
            return 0
        with self._conn() as conn:
            before = conn.execute("SELECT COUNT(*) FROM candles WHERE symbol=? AND timeframe=?",
                                  (symbol, timeframe)).fetchone()[0]
            conn.executemany(
                "INSERT OR IGNORE INTO candles (symbol, timeframe, ts, open, high, low, close, volume)"
                " VALUES (?,?,?,?,?,?,?,?)", rows)
            after = conn.execute("SELECT COUNT(*) FROM candles WHERE symbol=? AND timeframe=?",
                                 (symbol, timeframe)).fetchone()[0]
        return after - before

    def get(self, symbol: str, timeframe: str, limit: Optional[int] = None) -> List[dict]:
        """Oldest-to-newest bars. An empty list means genuinely nothing stored."""
        sql = ("SELECT ts, open, high, low, close, volume FROM candles "
               "WHERE symbol=? AND timeframe=? ORDER BY ts DESC")
        params: tuple = (symbol, timeframe)
        if limit:
            sql += " LIMIT ?"
            params = params + (int(limit),)
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [{"ts": r[0], "open": r[1], "high": r[2], "low": r[3],
                 "close": r[4], "volume": r[5]} for r in reversed(rows)]

    def last_ts(self, symbol: str, timeframe: str) -> Optional[int]:
        with self._conn() as conn:
            row = conn.execute("SELECT MAX(ts) FROM candles WHERE symbol=? AND timeframe=?",
                               (symbol, timeframe)).fetchone()
        return row[0] if row and row[0] is not None else None

    def stats(self) -> CacheStats:
        with self._conn() as conn:
            rows = conn.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), MAX(ts) FROM candles").fetchone()
        return CacheStats(rows=rows[0] or 0, symbols=rows[1] or 0, newest_ts=rows[2])

    def stale_hours(self, symbol: str, timeframe: str, now_ts: int) -> Optional[float]:
        """How old the newest stored bar is, in hours. None when nothing is stored."""
        last = self.last_ts(symbol, timeframe)
        if last is None:
            return None
        return round((now_ts - last) / 3600.0, 2)
