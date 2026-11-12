"""Alpha Vantage: the third price source and a second opinion on fundamentals.

Why a third source when two already exist: cross-checking. If Twelve Data and
Alpha Vantage disagree on a close price by more than a few basis points, one of
them is wrong and the data layer must say so instead of silently picking one.

Rules, same as every other adapter here:
  * a rate-limit notice ("Note" / "Information") raises, never returns empty
  * a missing fundamental becomes None, never 0.0
  * responses are cached on disk: the free tier is 25 requests per day
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..core.types import Candle

BASE = "https://www.alphavantage.co/query"


class AlphaVantageError(RuntimeError):
    """Raised when the provider refuses or returns something unusable."""


@dataclass(frozen=True)
class TimeSeriesMeta:
    symbol: str
    rows: int
    first_ts: int
    last_ts: int
    fetched_at: str
    source: str = "alphavantage"


def _key(api_key: Optional[str] = None) -> str:
    key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        raise AlphaVantageError("ALPHAVANTAGE_API_KEY is not set")
    return key


def _get(params: dict, api_key: Optional[str], cache: Optional[Path]) -> dict:
    params = dict(params)
    params["apikey"] = _key(api_key)
    if cache is not None and cache.exists():
        return json.loads(cache.read_text())
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "aurora-v2/0.3"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    for notice in ("Note", "Information"):
        if notice in payload:
            raise AlphaVantageError(f"provider limit: {payload[notice][:160]}")
    if "Error Message" in payload:
        raise AlphaVantageError(f"bad request: {payload['Error Message'][:160]}")
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(payload))
    return payload


def parse_daily(payload: dict, symbol: str) -> list[Candle]:
    series = payload.get("Time Series (Daily)")
    if not series:
        raise AlphaVantageError(f"{symbol}: no daily series in response")
    out: list[Candle] = []
    for day, row in series.items():
        try:
            o, h, l, c = (float(row[k]) for k in ("1. open", "2. high", "3. low", "4. close"))
        except (KeyError, TypeError, ValueError) as exc:
            raise AlphaVantageError(f"{symbol}: malformed row for {day}: {exc}") from exc
        vol = row.get("5. volume")
        ts = int(datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
        out.append(Candle(ts=ts, open=o, high=h, low=l, close=c,
                          volume=float(vol) if vol else 0.0))
    out.sort(key=lambda c: c.ts)
    return out


def fetch_daily(symbol: str, outputsize: str = "compact",
                cache_dir: str = "data_cache/alphavantage",
                api_key: Optional[str] = None) -> tuple[list[Candle], TimeSeriesMeta]:
    cache = Path(cache_dir) / f"{symbol}_{outputsize}.json"
    payload = _get({"function": "TIME_SERIES_DAILY", "symbol": symbol,
                    "outputsize": outputsize}, api_key, cache)
    candles = parse_daily(payload, symbol)
    if not candles:
        raise AlphaVantageError(f"{symbol}: empty series")
    ejected = datetime.now(timezone.utc).isoformat()
    meta = TimeSeriesMeta(symbol=symbol, rows=len(candles),
                          first_ts=candles[0].ts, last_ts=candles[-1].ts,
                          fetched_at=ejected)
    return candles, meta


FUNDAMENTAL_FIELDS = {
    "PERatio": "pe_ratio",
    "PEGRatio": "peg_ratio",
    "PriceToBookRatio": "pb_ratio",
    "ROE": "roe",
    "ReturnOnAssetsTTM": "roa",
    "OperatingMarginTTM": "operating_margin",
    "MarketCapitalization": "market_cap",
    "DividendYield": "dividend_yield",
    "Beta": "beta",
    "EPS": "eps",
}


def _num(value) -> Optional[float]:
    if value in (None, "", "None", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_overview(payload: dict) -> dict:
    if not payload or "Symbol" not in payload:
        raise AlphaVantageError("overview: no Symbol in response")
    out: dict = {"symbol": payload.get("Symbol"), "name": payload.get("Name"),
                 "sector": payload.get("Sector"), "industry": payload.get("Industry"),
                 "currency": payload.get("Currency"), "exchange": payload.get("Exchange")}
    for src, dst in FUNDAMENTAL_FIELDS.items():
        out[dst] = _num(payload.get(src))
    return out


def overview(symbol: str, cache_dir: str = "data_cache/alphavantage",
             api_key: Optional[str] = None) -> dict:
    cache = Path(cache_dir) / f"{symbol}_overview.json"
    return parse_overview(_get({"function": "OVERVIEW", "symbol": symbol}, api_key, cache))
