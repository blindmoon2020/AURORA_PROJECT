"""SEC EDGAR: point-in-time fundamentals with no vendor and no key.

EDGAR publishes every XBRL fact with the date it was filed, which is exactly the
field a backtest needs and exactly the field a "current ratios" API cannot give.
Free, official, and slower to parse - the right trade for a research platform.
"""
from __future__ import annotations

import gzip
import json
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

UA = "AURORA research platform (research@aurora.local)"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
CONCEPT = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json"
CACHE = Path("data_cache/edgar")


class EdgarError(RuntimeError):
    pass


def _get(url: str, cache: Path, max_age_hours: float = 168.0) -> dict:
    if cache.exists() and (time.time() - cache.stat().st_mtime) / 3600 < max_age_hours:
        return json.loads(cache.read_text())
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                              "Accept-Encoding": "gzip, deflate"})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)      # EDGAR always compresses; ignoring this
            payload = json.loads(raw.decode("utf-8"))   # is a silent parse failure
    except Exception as exc:
        raise EdgarError(f"EDGAR fetch failed: {exc}") from exc
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload))
    return payload


def cik_map() -> Dict[str, str]:
    payload = _get(TICKERS_URL, CACHE / "tickers.json", max_age_hours=24 * 7)
    out = {}
    for row in payload.values():
        out[str(row["ticker"]).upper()] = str(row["cik_str"]).zfill(10)
    return out


def eps_points(symbol: str) -> List[dict]:
    """Diluted EPS with its filing date; falls back to basic when diluted is absent."""
    cik = cik_map().get(symbol.upper())
    if not cik:
        raise EdgarError(f"{symbol}: no CIK registered with the SEC")
    for concept in ("EarningsPerShareDiluted", "EarningsPerShareBasic"):
        try:
            payload = _get(CONCEPT.format(cik=cik, concept=concept),
                           CACHE / f"{symbol}_{concept}.json")
        except EdgarError:
            continue
        units = payload.get("units", {})
        rows = units.get("USD/shares") or next(iter(units.values()), [])
        out = [{"end": r.get("end"), "filed": r.get("filed"), "eps": r.get("val")}
               for r in rows if r.get("val") is not None and r.get("filed")]
        if out:
            out.sort(key=lambda r: r["filed"])
            return out
    raise EdgarError(f"{symbol}: no EPS facts on EDGAR")
