"""Tiingo daily bars, with corporate actions applied.

The reason this source exists next to Yahoo and Twelve Data is one column:
`adjClose`. A split is not a price move, and a backtest that sees a 4:1 split as
a -75% day invents a signal out of an accounting event. So OHLC is rescaled by
adjClose/close on every bar, which yields a total-return series.

Options:
  adjusted=True   total-return series (default) - use this for backtests
  adjusted=False  raw prices as printed - use only to compare against a feed

Errors: a 401/403 or a provider message raises TiingoError. An empty list is
returned only when the provider genuinely has no bars for that window.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from ..core.types import Candle

BASE = "https://api.tiingo.com/tiingo"
CACHE = Path("data_cache/tiingo")


class TiingoError(RuntimeError):
    """Raised when Tiingo refuses a request or answers with an error payload."""


@dataclass(frozen=True)
class TiingoMeta:
    ticker: str
    rows: int
    first_ts: int
    last_ts: int
    adjusted: bool
    fetched_at: str


def _key() -> str:
    key = (os.environ.get("TIINGO_API_KEY") or "").strip()
    if not key:
        raise TiingoError("TIINGO_API_KEY is not set")
    return key


def _ts(date_str: str) -> int:
    """Tiingo sends '2026-11-11T00:00:00.000Z'; keep it UTC, drop the clock."""
    return int(datetime.strptime(date_str[:10], "%Y-%m-%d")
               .replace(tzinfo=timezone.utc).timestamp())


def _get(path: str, params: dict[str, Any]) -> Any:
    params = dict(params)
    params["token"] = _key()
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise TiingoError(f"HTTP {exc.code} for {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise TiingoError(f"network error for {path}: {exc.reason}") from exc
    if isinstance(payload, dict) and payload.get("detail"):
        raise TiingoError(f"provider says: {payload['detail'][:200]}")
    return payload


def _cache_path(kind: str, key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:80]
    return CACHE / f"{kind}_{safe}.json"


def _cached(kind: str, key: str, loader, max_age_hours: float = 6.0):
    path = _cache_path(kind, key)
    if path.exists():
        age = time.time() - path.stat().st_mtime
        if age < max_age_hours * 3600:
            return json.loads(path.read_text(encoding="utf-8"))
    data = loader()
    if data:                                  # never cache an empty answer
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    return data


def _scale(row: dict[str, float], adjust: float) -> Tuple[float, float, float, float]:
    return (row["open"] * adjust, row["high"] * adjust,
            row["low"] * adjust, row["close"] * adjust)


def parse_rows(rows: Sequence[dict[str, Any]], adjusted: bool = True) -> List[Candle]:
    """Turn Tiingo rows into Candles, rescaling OHLC when adjusted=True."""
    out: List[Candle] = []
    for row in sorted(rows, key=lambda r: r["date"]):
        close = float(row["close"])
        adj = float(row.get("adjClose") or close)
        adjust = (adj / close) if (adjusted and close) else 1.0
        o, h, l, c = _scale({"open": float(row["open"]), "high": float(row["high"]),
                             "low": float(row["low"]), "close": close}, adjust)
        out.append(Candle(ts=_ts(row["date"]), open=o, high=h, low=l, close=c,
                          volume=float(row.get("volume") or 0.0)))
    return out


def fetch_daily(ticker: str, start: Optional[str] = None, end: Optional[str] = None,
                adjusted: bool = True) -> Tuple[List[Candle], TiingoMeta]:
    """Daily bars for one ticker. `start`/`end` are 'YYYY-MM-DD'."""
    params: dict[str, Any] = {}
    if start:
        params["startDate"] = start
    if end:
        params["endDate"] = end
    cache_key = f"{ticker}_{start or 'first'}_{end or 'last'}_{int(adjusted)}"

    def load():
        return _get(f"daily/{ticker}/prices", params)   # /prices is the series; the bare path is metadata

    rows = _cached("daily", cache_key, load)
    if not isinstance(rows, list):
        raise TiingoError(f"unexpected payload for {ticker}: {type(rows).__name__}")
    candles = parse_rows(rows, adjusted=adjusted)
    meta = TiingoMeta(
        ticker=ticker, rows=len(candles),
        first_ts=candles[0].ts if candles else 0,
        last_ts=candles[-1].ts if candles else 0,
        adjusted=adjusted,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return candles, meta


def metadata(ticker: str) -> dict[str, Any]:
    """Ticker description: name, exchange, first and last bar available."""
    def load():
        return _get(f"daily/{ticker}", {})   # metadata lives on the bare path

    payload = _cached("meta", ticker, load, max_age_hours=24 * 7)
    if not isinstance(payload, dict):
        raise TiingoError(f"unexpected metadata for {ticker}")
    return payload


def news(tickers: Sequence[str], limit: int = 10) -> List[dict[str, Any]]:
    """Recent headlines. Free plan is limited, so failures stay loud."""
    def load():
        return _get("news", {"tickers": ",".join(tickers), "limit": limit})

    payload = _cached("news", "-".join(tickers) + f"_{limit}", load, max_age_hours=1)
    if isinstance(payload, dict) and payload.get("detail"):
        raise TiingoError(f"provider says: {payload['detail'][:160]}")
    return payload if isinstance(payload, list) else []
