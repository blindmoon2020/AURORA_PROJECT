"""Fundamentals and company data from Finnhub.

Two rules that keep this honest:
  * a metric Finnhub does not send becomes None, never 0.0 (a missing P/E is not a
    cheap stock)
  * every response is cached on disk, so a research run is reproducible and the
    free tier's rate limit is not spent twice on the same question
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Deque, Dict, List, Optional

BASE = "https://finnhub.io/api/v1"
CACHE = Path("data_cache/finnhub")


class FinnhubError(RuntimeError):
    pass


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Optional[float]
    change_pct: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    ts: Optional[int]


@dataclass(frozen=True)
class Profile:
    symbol: str
    name: Optional[str]
    industry: Optional[str]
    market_cap_musd: Optional[float]
    currency: Optional[str]
    exchange: Optional[str]


@dataclass(frozen=True)
class Fundamentals:
    symbol: str
    pe_ttm: Optional[float] = None
    pb: Optional[float] = None
    ps_ttm: Optional[float] = None
    roe_ttm: Optional[float] = None
    net_margin_ttm: Optional[float] = None
    dividend_yield_pct: Optional[float] = None
    beta: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None


def _key() -> str:
    key = os.environ.get("FINNHUB_API_KEY", "").strip()
    if not key:
        raise FinnhubError("FINNHUB_API_KEY is not set; add it through the secret form")
    return key


def _num(m: Dict[str, object], name: str) -> Optional[float]:
    v = m.get(name)
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return f


def parse_quote(symbol: str, payload: Dict[str, object]) -> Quote:
    def g(k: str) -> Optional[float]:
        v = payload.get(k)
        return float(v) if isinstance(v, (int, float)) else None

    price = g("c")
    if price == 0.0:
        price = None          # Finnhub returns 0 for an unknown ticker
    return Quote(symbol=symbol, price=price, change_pct=g("dp"), high=g("h"),
                 low=g("l"), prev_close=g("pc"), ts=int(g("t") or 0) or None)


def parse_profile(symbol: str, payload: Dict[str, object]) -> Profile:
    cap = payload.get("marketCapitalization")
    return Profile(
        symbol=symbol,
        name=payload.get("name") or None,           # type: ignore[arg-type]
        industry=payload.get("finnhubIndustry") or None,  # type: ignore[arg-type]
        market_cap_musd=float(cap) if isinstance(cap, (int, float)) else None,
        currency=payload.get("currency") or None,   # type: ignore[arg-type]
        exchange=payload.get("exchange") or None,   # type: ignore[arg-type]
    )


def parse_fundamentals(symbol: str, payload: Dict[str, object]) -> Fundamentals:
    m = payload.get("metric") or {}
    if not isinstance(m, dict):
        m = {}
    return Fundamentals(
        symbol=symbol,
        pe_ttm=_num(m, "peTTM"),
        pb=_num(m, "pbAnnual"),
        ps_ttm=_num(m, "psTTM"),
        roe_ttm=_num(m, "roeTTM"),
        net_margin_ttm=_num(m, "netProfitMarginTTM"),
        dividend_yield_pct=_num(m, "dividendYieldIndicatedAnnual"),
        beta=_num(m, "beta"),
        week52_high=_num(m, "52WeekHigh"),
        week52_low=_num(m, "52WeekLow"),
    )


class Finnhub:
    """Thin, cached client. Free tier is 60 calls/minute, so calls are paced."""

    def __init__(self, cache_dir: Path = CACHE, calls_per_minute: int = 50) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.calls_per_minute = calls_per_minute
        self.hits: Deque[float] = deque()

    def _throttle(self) -> None:
        now = time.monotonic()
        while self.hits and now - self.hits[0] > 60:
            self.hits.popleft()
        if len(self.hits) >= self.calls_per_minute:
            time.sleep(60 - (now - self.hits[0]) + 0.05)
            self.hits.popleft()
        self.hits.append(time.monotonic())

    def _get(self, path: str, params: Dict[str, str], cache_key: str,
             max_age_hours: float = 12.0) -> Dict[str, object]:
        cached = self.cache_dir / f"{cache_key}.json"
        if cached.exists():
            age = time.time() - cached.stat().st_mtime
            if age < max_age_hours * 3600:
                return json.loads(cached.read_text())

        query = dict(params, token=_key())
        url = f"{BASE}{path}?{urllib.parse.urlencode(query)}"
        self._throttle()
        req = urllib.request.Request(url, headers={"User-Agent": "aurora-research/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.loads(resp.read().decode())
        except Exception as exc:                      # network, 401, 429, ...
            raise FinnhubError(f"finnhub {path} failed: {exc}") from exc
        if isinstance(payload, dict) and payload.get("error"):
            raise FinnhubError(f"finnhub {path}: {payload['error']}")
        cached.write_text(json.dumps(payload))
        return payload

    def quote(self, symbol: str) -> Quote:
        return parse_quote(symbol, self._get("/quote", {"symbol": symbol},
                                             f"quote_{symbol}", max_age_hours=0.5))

    def profile(self, symbol: str) -> Profile:
        return parse_profile(symbol, self._get("/stock/profile2", {"symbol": symbol},
                                               f"profile_{symbol}"))

    def fundamentals(self, symbol: str) -> Fundamentals:
        payload = self._get("/stock/metric", {"symbol": symbol, "metric": "all"},
                            f"metric_{symbol}", max_age_hours=24.0)
        return parse_fundamentals(symbol, payload)

    def news(self, symbol: str, days: int = 7) -> List[Dict[str, object]]:
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days)
        payload = self._get("/company-news",
                            {"symbol": symbol, "from": start.isoformat(),
                             "to": today.isoformat()},
                            f"news_{symbol}_{start.isoformat()}_{today.isoformat()}",
                            max_age_hours=1.0)
        if not isinstance(payload, list):
            return []
        return sorted(payload, key=lambda n: n.get("datetime") or 0, reverse=True)


def market_session_note() -> str:
    """A small honesty helper: quote staleness is not the same as a live price."""
    return date.today().isoformat()
