"""Twelve Data: the multi-symbol price feed, normalised into the same Candle type.

Rules:
  * timestamps are requested in UTC and stored as epoch seconds
  * a response that is not a real series (rate limit, bad symbol, plan limit)
    raises TwelveDataError instead of returning an empty list that looks like
    "no data"
  * every response is cached, because the free tier is 800 credits/day and a
    research run must be reproducible tomorrow
  * volume is kept when the venue sends it (equities, crypto) and zero when it
    does not (spot FX), never invented

Free-tier reality: 800 credits/day, ~8 requests/minute. A 5000-bar series costs
several credits, so the cache is not an optimisation, it is the only way a
multi-symbol study finishes inside a day.
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
from typing import Dict, List, Optional, Sequence

from ..core.types import Candle, candle

BASE = "https://api.twelvedata.com"
DEFAULT_CACHE = Path("data_cache") / "twelvedata"

# our interval names -> Twelve Data interval names
INTERVALS = {
    "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1h", "4h": "4h", "1d": "1day", "1w": "1week",
}


class TwelveDataError(RuntimeError):
    """The API refused the request, or returned something that is not a series."""


@dataclass(frozen=True)
class SeriesMeta:
    symbol: str
    interval: str
    rows: int
    first_ts: int
    last_ts: int
    cached: bool
    source: str = "twelvedata"


def _api_key() -> str:
    key = os.environ.get("TWELVEDATA_API_KEY", "").strip()
    if not key:
        raise TwelveDataError(
            "TWELVEDATA_API_KEY is not set; add it through the secret form"
        )
    return key


def parse_time_series(payload: dict) -> List[Candle]:
    """Turn a Twelve Data time_series payload into candles, oldest first."""
    if not isinstance(payload, dict):
        raise TwelveDataError(f"unexpected payload: {type(payload).__name__}")
    if payload.get("status") == "error" or ("code" in payload and "values" not in payload):
        raise TwelveDataError(
            f"API error {payload.get('code')}: {payload.get('message')}"
        )
    values = payload.get("values")
    if values is None:
        raise TwelveDataError(f"no values in response: {str(payload)[:200]}")

    candles: List[Candle] = []
    for row in values:
        try:
            stamp = row["datetime"]
            fmt = "%Y-%m-%d %H:%M:%S" if " " in stamp else "%Y-%m-%d"
            ts = int(datetime.strptime(stamp, fmt).replace(tzinfo=timezone.utc).timestamp())
            o, h, l, c = (float(row[k]) for k in ("open", "high", "low", "close"))
        except (KeyError, TypeError, ValueError) as exc:
            raise TwelveDataError(f"bad row {row!r}: {exc}") from exc
        vol = row.get("volume")
        try:
            volume = float(vol) if vol not in (None, "") else 0.0
        except (TypeError, ValueError):
            volume = 0.0
        candles.append(candle(ts=ts, open=o, high=h, low=l, close=c, volume=volume))

    candles.sort(key=lambda c: c.ts)
    return candles


def _get(path: str, params: Dict[str, str]) -> dict:
    params = dict(params)
    params["apikey"] = _api_key()
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "aurora-v2/0.3"})
    try:
        with urllib.request.urlopen(req, timeout=30) as fh:
            return json.loads(fh.read().decode())
    except urllib.error.HTTPError as exc:
        raise TwelveDataError(f"HTTP {exc.code} for {path}") from exc
    except urllib.error.URLError as exc:
        raise TwelveDataError(f"network error for {path}: {exc.reason}") from exc


def fetch_time_series(
    symbol: str,
    interval: str = "1h",
    outputsize: int = 5000,
    cache_dir: str | Path = DEFAULT_CACHE,
    use_cache: bool = True,
) -> tuple[List[Candle], SeriesMeta]:
    if interval not in INTERVALS:
        raise TwelveDataError(f"unsupported interval {interval!r}; use one of {sorted(INTERVALS)}")
    cache_dir = Path(cache_dir)
    cache_file = cache_dir / f"{symbol.replace('/', '_')}_{interval}.json"

    if use_cache and cache_file.exists():
        blob = json.loads(cache_file.read_text())
        candles = [Candle(**row) for row in blob["candles"]]
        meta = SeriesMeta(symbol=symbol, interval=interval, rows=len(candles),
                          first_ts=candles[0].ts if candles else 0,
                          last_ts=candles[-1].ts if candles else 0, cached=True)
        return candles, meta

    payload = _get("time_series", {
        "symbol": symbol,
        "interval": INTERVALS[interval],
        "outputsize": str(outputsize),
        "timezone": "UTC",
        "order": "ASC",
    })
    candles = parse_time_series(payload)
    if not candles:
        raise TwelveDataError(f"{symbol} {interval}: empty series")

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps({
        "symbol": symbol,
        "interval": interval,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "candles": [c.__dict__ for c in candles],
    }))
    meta = SeriesMeta(symbol=symbol, interval=interval, rows=len(candles),
                      first_ts=candles[0].ts, last_ts=candles[-1].ts, cached=False)
    return candles, meta


def fetch_many(
    symbols: Sequence[str],
    interval: str = "1d",
    outputsize: int = 5000,
    cache_dir: str | Path = DEFAULT_CACHE,
    pause: float = 8.0,
) -> Dict[str, List[Candle]]:
    """Fetch several symbols, pausing between calls to respect the free tier."""
    out: Dict[str, List[Candle]] = {}
    fresh = 0
    for sym in symbols:
        candles, meta = fetch_time_series(sym, interval, outputsize, cache_dir)
        out[sym] = candles
        if not meta.cached:
            fresh += 1
            if fresh > 1:
                time.sleep(pause)
    return out
