"""Free daily/hourly FX bars from Yahoo's chart endpoint, with provenance.

Not a market data vendor: bars can be missing, duplicated or revised, and the
history window is capped by the interval. That is acceptable for research as
long as every report states where the numbers came from and how clean they were.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..core.types import Candle

BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
UA = "Mozilla/5.0 (compatible; aurora-v2 research; +https://github.com/blindmoon2020)"


class YahooError(RuntimeError):
    pass


@dataclass
class FetchMeta:
    symbol: str
    interval: str
    range: str
    url: str
    fetched_at: str
    rows_raw: int = 0
    rows_kept: int = 0
    first_ts: Optional[int] = None
    last_ts: Optional[int] = None
    drop_reasons: dict = field(default_factory=dict)


def cache_path(cache_dir: str | Path, symbol: str, interval: str, range_: str) -> Path:
    safe = symbol.replace("=", "").replace("/", "_")
    return Path(cache_dir) / f"{safe}_{interval}_{range_}.json"


def fetch_yahoo(
    symbol: str = "EURUSD=X",
    interval: str = "1h",
    range_: str = "730d",
    cache_dir: str | Path = "data_cache",
    offline: bool = False,
) -> tuple[List[Candle], FetchMeta]:
    """Download (or load from cache) one series. Cache is written after a fetch."""
    url = BASE.format(symbol=symbol) + f"?range={range_}&interval={interval}"
    path = cache_path(cache_dir, symbol, interval, range_)
    payload: Optional[dict] = None

    if offline or path.exists():
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8")).get("raw")
        elif offline and not path.exists():
            raise YahooError(f"offline and no cache at {path}")

    if payload is None:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if path.exists():  # stale cache beats no data
                payload = json.loads(path.read_text(encoding="utf-8")).get("raw")
            else:
                raise YahooError(f"fetch failed for {symbol} {interval}: {exc}") from exc
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"fetched_at": datetime.now(timezone.utc).isoformat(),
                            "url": url, "raw": payload}),
                encoding="utf-8",
            )

    try:
        result = payload["chart"]["result"][0]
        ts_list = result["timestamp"]
        quote = result["indicators"]["quote"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise YahooError(f"unexpected payload shape for {symbol}: {exc}") from exc

    meta = FetchMeta(
        symbol=symbol, interval=interval, range=range_, url=url,
        fetched_at=datetime.now(timezone.utc).isoformat(), rows_raw=len(ts_list),
    )
    candles: List[Candle] = []
    for i, ts in enumerate(ts_list):
        o, h, l, c = (quote.get(k, [None] * len(ts_list))[i]
                      for k in ("open", "high", "low", "close"))
        if None in (o, h, l, c) or min(o, h, l, c) <= 0:
            key = "null_or_nonpositive"
            meta.drop_reasons[key] = meta.drop_reasons.get(key, 0) + 1
            continue
        hi, lo = max(o, h, l, c), min(o, h, l, c)
        if (hi, lo) != (h, l):
            key = "ohlc_inconsistent"
            meta.drop_reasons[key] = meta.drop_reasons.get(key, 0) + 1
        try:
            candles.append(Candle(ts=int(ts), open=float(o), high=float(hi),
                                  low=float(lo), close=float(c)))
        except ValueError:
            key = "invalid_bar"
            meta.drop_reasons[key] = meta.drop_reasons.get(key, 0) + 1

    if not candles:
        raise YahooError(f"no usable bars for {symbol} {interval}")
    meta.rows_kept = len(candles)
    meta.first_ts, meta.last_ts = candles[0].ts, candles[-1].ts
    return candles, meta
