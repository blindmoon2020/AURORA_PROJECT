"""Financial Modeling Prep: statements with a filing date, which is the whole point.

Finnhub gives today's ratios. That is useless for a backtest, because a 2026
statement tells you nothing about what was knowable in 2019. FMP's income
statement carries both `date` (period end) and `filingDate` (when the market could
first see it), so a snapshot can expose `available_from_ts` and the backtest can
refuse to look early. That single field is why this source exists.

Measured on the free plan (2026-11-12):
  /api/v3/*            -> 403, legacy path is closed to new keys
  /stable/profile      -> works
  /stable/quote        -> works
  /stable/income-statement -> works, includes filingDate
  /stable/company-screener -> 402 payment required
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
from typing import Any, Dict, List, Optional

BASE = "https://financialmodelingprep.com/stable"
CACHE = Path("data_cache/fmp")


class FmpError(RuntimeError):
    """Raised for errors, never for an empty result."""


@dataclass(frozen=True)
class Snapshot:
    """One fundamentals snapshot, with the moment it became public."""

    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: Optional[float]
    beta: Optional[float]
    revenue: Optional[float]
    net_income: Optional[float]
    period_end: Optional[str]
    filing_date: Optional[str]

    @property
    def available_from_ts(self) -> Optional[int]:
        """Epoch seconds from which this snapshot may be used. None = do not use."""
        raw = self.filing_date or self.period_end
        if not raw:
            return None
        try:
            return int(datetime.strptime(raw[:10], "%Y-%m-%d")
                       .replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            return None


def _key() -> str:
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        raise FmpError("FMP_API_KEY is not set")
    return key


def _get(path: str, params: Dict[str, Any]) -> Any:
    params = dict(params)
    params["apikey"] = _key()
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 402:
            raise FmpError(f"plan limit on {path}: this endpoint needs a paid plan") from exc
        if exc.code in (401, 403):
            raise FmpError(f"not authorised on {path}: check FMP_API_KEY") from exc
        if exc.code == 429:
            raise FmpError(f"rate limit on {path}: slow down or cache") from exc
        raise FmpError(f"HTTP {exc.code} on {path}") from exc
    except urllib.error.URLError as exc:
        raise FmpError(f"network error on {path}: {exc.reason}") from exc


def _cached(name: str, loader) -> Any:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    if path.exists() and time.time() - path.stat().st_mtime < 86_400:
        return json.loads(path.read_text(encoding="utf-8"))
    data = loader()
    if data:                      # never cache an empty answer: it looks like "no such symbol"
        path.write_text(json.dumps(data), encoding="utf-8")
    return data


def search_symbols(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """Ticker search, for building the instrument master without a paid listing.

    Free plan matches ticker prefixes only: "AAPL" works, "apple" does not.
    """
    def load() -> Any:
        # free plan matches tickers, not company names: try the query as typed, then upper-cased
        for attempt in (query, query.upper()):
            payload = _get("search-symbol", {"query": attempt, "limit": limit})
            if isinstance(payload, list) and payload:
                return payload
        return []

    data = _cached(f"search_{query.lower().replace('/', '_')}", load)
    if not isinstance(data, list):
        raise FmpError("unexpected payload for search-symbol")
    return [{"symbol": str(row.get("symbol", "")),
             "name": str(row.get("name", "")),
             "currency": str(row.get("currency", "")),
             "exchange": str(row.get("exchangeFullName") or row.get("exchange", ""))}
            for row in data[:limit]]


def profile(symbol: str) -> Dict[str, Any]:
    data = _cached(f"profile_{symbol}", lambda: _get("profile", {"symbol": symbol}))
    if not isinstance(data, list) or not data:
        raise FmpError(f"no profile for {symbol}")
    return data[0]


def income_statement(symbol: str, limit: int = 4) -> List[Dict[str, Any]]:
    data = _cached(f"income_{symbol}_{limit}",
                   lambda: _get("income-statement", {"symbol": symbol, "limit": limit}))
    if not isinstance(data, list):
        raise FmpError(f"unexpected payload for income-statement {symbol}")
    return data


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def snapshot(symbol: str) -> Snapshot:
    """Latest profile joined to the most recent statement, carrying filingDate."""
    prof = profile(symbol)
    statements = income_statement(symbol, limit=1)
    stmt = statements[0] if statements else {}
    return Snapshot(
        symbol=symbol,
        name=str(prof.get("companyName") or prof.get("name") or symbol),
        sector=str(prof.get("sector") or ""),
        industry=str(prof.get("industry") or ""),
        market_cap=_num(prof.get("marketCap")),
        beta=_num(prof.get("beta")),
        revenue=_num(stmt.get("revenue")),
        net_income=_num(stmt.get("netIncome")),
        period_end=stmt.get("date"),
        filing_date=stmt.get("filingDate") or stmt.get("acceptedDate"),
    )
