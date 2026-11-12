"""EODHD: the long-history, world-breadth source.

What it adds over the other adapters is depth and coverage: 30+ years and every
exchange plus FX, crypto and indices on one symbol format. On the free plan the
depth is one year, so `coverage()` exists to tell a caller what it actually got
instead of letting a backtest quietly run on 251 bars.

Prices are adjusted. Open, high and low are scaled by the same factor as the
close, so a split does not leave a bar whose high is below its adjusted close.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional, Sequence

from ..core.types import Candle

BASE = "https://eodhd.com/api/eod"


class EODHDError(RuntimeError):
    pass


def normalise(ticker: str, exchange: Optional[str] = None) -> str:
    """EODHD wants TICKER.EXCHANGE; a bare ticker defaults to US."""
    if "." in ticker:
        return ticker.upper()
    return f"{ticker.upper()}.{(exchange or 'US').upper()}"


def parse_eod(payload) -> List[Candle]:
    """Build adjusted candles from EODHD's rows, refusing anything malformed."""
    if isinstance(payload, dict):
        raise EODHDError(f"EODHD error: {str(payload.get('error') or payload)[:160]}")
    if not isinstance(payload, list):
        raise EODHDError(f"unexpected payload type {type(payload).__name__}")
    if payload and isinstance(payload[0], str):
        raise EODHDError(f"EODHD error: {payload[0][:160]}")

    out: List[Candle] = []
    for row in payload:
        try:
            ts = int(time.mktime(time.strptime(row["date"], "%Y-%m-%d")))
            raw_close = float(row["close"])
            adj = row.get("adjusted_close")
            adj = float(adj) if adj not in (None, "") else raw_close
            ratio = (adj / raw_close) if raw_close > 0 else 1.0
            out.append(Candle(
                ts=ts,
                open=float(row["open"]) * ratio,
                high=float(row["high"]) * ratio,
                low=float(row["low"]) * ratio,
                close=adj,
                volume=float(row.get("volume") or 0.0),
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise EODHDError(f"malformed row {row!r}: {exc}") from exc
    out.sort(key=lambda c: c.ts)
    return out


def fetch_eod(
    ticker: str,
    exchange: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    cache_dir: str | Path = "data_cache",
    max_age_hours: float = 12.0,
) -> List[Candle]:
    symbol = normalise(ticker, exchange)
    cache = Path(cache_dir) / f"eodhd_{symbol.replace('.', '_')}_{start or 'all'}_{end or 'all'}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) / 3600 < max_age_hours:
        return parse_eod(json.loads(cache.read_text()))

    key = os.environ.get("EODHD_API_KEY", "").strip()
    if not key:
        raise EODHDError("EODHD_API_KEY is not set; add it in the secret form")
    params = {"api_token": key, "fmt": "json", "order": "a"}
    if start:
        params["from"] = start
    if end:
        params["to"] = end
    url = f"{BASE}/{symbol}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except Exception as exc:
        raise EODHDError(f"fetch {symbol} failed: {exc}") from exc

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload))
    return parse_eod(payload)


def coverage(candles: Sequence[Candle]) -> dict:
    """What the caller really received: bars and years, so depth is never assumed."""
    if not candles:
        return {"bars": 0, "years": 0.0}
    span = (candles[-1].ts - candles[0].ts) / (365.25 * 86400)
    return {"bars": len(candles), "years": round(span, 2)}
