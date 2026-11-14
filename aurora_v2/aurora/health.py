"""One command that answers: can this machine actually fetch every source today?

A pipeline that fails silently is worse than one that fails loudly, because the
backtest still produces a number. Each source is reported on three facts - is the
credential present, how old is the last cached response, and is it usable at all -
so a missing key looks different from a key whose data has gone stale.
"""
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

# name -> (credential env var or None for keyless, cache glob)
SOURCES: Dict[str, tuple] = {
    "fred": ("FRED_API_KEY", "*fred*.json"),
    "twelvedata": ("TWELVEDATA_API_KEY", "*_1d.json"),
    "finnhub": ("FINNHUB_API_KEY", "*finnhub*.json"),
    "fmp": ("FMP_API_KEY", "*fmp*.json"),
    "eodhd": ("EODHD_API_KEY", "*eodhd*.json"),
    "tiingo": ("TIINGO_API_KEY", "*tiingo*.json"),
    "alphavantage": ("ALPHAVANTAGE_API_KEY", "*alpha*.json"),
    "edgar": (None, "*edgar*.json"),
    "yahoo": (None, "*_1d_20y.json"),
    "tsetmc": (None, "*tsetmc*.csv"),
}

STALE_AFTER_DAYS = 7.0


def cache_age_days(cache_dir: Path, pattern: str, now: Optional[float] = None) -> Optional[float]:
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        return None
    files = list(cache_dir.glob(pattern))
    if not files:
        return None
    newest = max(f.stat().st_mtime for f in files)
    now = time.time() if now is None else now
    return max(0.0, (now - newest) / 86400.0)


def source_rows(cache_dir: Path, env: Optional[Dict[str, str]] = None,
                now: Optional[float] = None) -> List[dict]:
    env = os.environ if env is None else env
    rows = []
    for name, (key_env, pattern) in SOURCES.items():
        has_key = None if key_env is None else bool(env.get(key_env))
        age = cache_age_days(cache_dir, pattern, now=now)
        if key_env is not None and not has_key:
            status, note = "no credential", "cannot fetch at all"
        elif age is None:
            status, note = "no cache", "never fetched on this machine"
        elif age > STALE_AFTER_DAYS:
            status, note = "stale", f"last response {age:.0f} days old"
        else:
            status, note = "ok", f"cached {age:.1f} days ago"
        rows.append({"source": name, "credential": has_key, "age_days": age,
                     "status": status, "note": note})
    return rows


def verdict(rows: List[dict]) -> tuple:
    """(usable, degraded, blocked) counts, plus the names that block a run."""
    usable = [r for r in rows if r["status"] == "ok"]
    degraded = [r for r in rows if r["status"] == "stale"]
    blocked = [r["source"] for r in rows if r["status"] in ("no credential", "no cache")]
    return len(usable), len(degraded), blocked
