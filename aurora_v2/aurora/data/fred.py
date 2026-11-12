"""Macro data from FRED, with the same discipline as price data.

Rules:
  * a missing observation ("." in FRED) is skipped, never filled with zero
  * every series carries its own release lag, so callers can avoid look-ahead
  * values are cached to disk with the fetch time, so a rerun is reproducible
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

API = "https://api.stlouisfed.org/fred/series/observations"


@dataclass(frozen=True)
class MacroPoint:
    date: str          # YYYY-MM-DD as FRED reports it
    value: float


#: series we actually use, with the lag before the value is public knowledge.
MACRO_SERIES: Dict[str, Dict[str, object]] = {
    "DGS10": {"name": "US 10y treasury yield", "unit": "pct", "lag_days": 1},
    "DGS2": {"name": "US 2y treasury yield", "unit": "pct", "lag_days": 1},
    "T10Y2Y": {"name": "10y minus 2y spread (curve)", "unit": "pct", "lag_days": 1},
    "DFF": {"name": "fed funds effective rate", "unit": "pct", "lag_days": 1},
    "CPIAUCSL": {"name": "CPI all urban consumers", "unit": "index", "lag_days": 45},
    "UNRATE": {"name": "unemployment rate", "unit": "pct", "lag_days": 30},
    "DTWEXBGS": {"name": "trade-weighted broad dollar index", "unit": "index", "lag_days": 7},
    "VIXCLS": {"name": "VIX close", "unit": "index", "lag_days": 1},
    "BAMLH0A0HYM2": {"name": "US high-yield credit spread", "unit": "pct", "lag_days": 1},
    "DCOILWTICO": {"name": "WTI spot", "unit": "usd", "lag_days": 3},
    "GOLDPMGBD228NLBM": {"name": "gold London PM fix", "unit": "usd", "lag_days": 1},
    "IRLTLT01IRM156N": {"name": "Iran long-term government bond yield", "unit": "pct", "lag_days": 60},
}


class FredError(RuntimeError):
    pass


def _key() -> str:
    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        raise FredError("FRED_API_KEY is not set; add it in the secret form")
    return key


def parse_observations(payload: dict) -> List[MacroPoint]:
    """FRED returns '.' for holidays and not-yet-published dates. Those are skipped."""
    out: List[MacroPoint] = []
    for obs in payload.get("observations", []):
        raw = obs.get("value")
        if raw in (None, "", "."):
            continue
        try:
            out.append(MacroPoint(date=obs["date"], value=float(raw)))
        except (KeyError, TypeError, ValueError):
            continue
    out.sort(key=lambda p: p.date)
    return out


def fetch_series(series_id: str, start: Optional[str] = None,
                 cache_dir: str | Path = "data_cache",
                 max_age_hours: float = 12.0) -> List[MacroPoint]:
    cache = Path(cache_dir) / f"fred_{series_id}.json"
    if cache.exists() and (time.time() - cache.stat().st_mtime) / 3600 < max_age_hours:
        return parse_observations(json.loads(cache.read_text()))

    params = {"series_id": series_id, "api_key": _key(), "file_type": "json"}
    if start:
        params["observation_start"] = start
    url = f"{API}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except Exception as exc:  # network, 4xx, bad json
        raise FredError(f"fetch {series_id} failed: {exc}") from exc

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload))
    return parse_observations(payload)


def latest(series_id: str, **kwargs) -> Optional[MacroPoint]:
    points = fetch_series(series_id, **kwargs)
    return points[-1] if points else None


def curve_snapshot(**kwargs) -> Dict[str, Optional[float]]:
    """The shape institutions look at first: level, slope, and stress."""
    snap: Dict[str, Optional[float]] = {}
    for sid in ("DGS10", "DGS2", "T10Y2Y", "VIXCLS", "BAMLH0A0HYM2", "DTWEXBGS"):
        p = latest(sid, **kwargs)
        snap[sid] = p.value if p else None
    return snap
