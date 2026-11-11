"""Instrument master: one canonical id per tradable thing, one data symbol, one truth.

Scope is deliberately a seed universe, not a claim of completeness: "every stock on
every exchange" is a listing of ~60k instruments that must come from a vendor feed,
not from a hand-written dict. The contract here is what matters: `Instrument` +
`load_listing()` so a full listing drops in without touching the rest of the code.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ASSET_CLASSES = ("fx", "metal", "energy", "agri", "index", "equity", "etf", "bond", "crypto")


@dataclass(frozen=True)
class Instrument:
    symbol: str            # canonical id, e.g. "EURUSD", "XAUUSD", "AAPL"
    yahoo: str             # data symbol for the current feed
    name: str
    asset_class: str
    region: str
    currency: str = "USD"
    has_volume: bool = False   # volume profile is only valid where volume is real
    session: str = "24x5"

    def __post_init__(self):
        if self.asset_class not in ASSET_CLASSES:
            raise ValueError(f"{self.symbol}: unknown asset_class {self.asset_class!r}")


def _fx() -> List[Instrument]:
    """G10 crosses plus the liquid EM pairs. Yahoo uses EURUSD=X."""
    g10 = ["EUR", "USD", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK"]
    out = []
    for base in g10:
        for quote in g10:
            if base == quote:
                continue
            out.append(Instrument(f"{base}{quote}", f"{base}{quote}=X", f"{base}/{quote}",
                                  "fx", "global"))
    em = ["MXN", "ZAR", "TRY", "CNH", "BRL", "INR", "KRW", "SGD", "PLN", "HUF",
          "CZK", "ILS", "THB", "PHP", "IDR", "CLP", "COP", "DKK"]
    out += [Instrument(f"USD{c}", f"USD{c}=X", f"USD/{c}", "fx", "em") for c in em]
    return out


def _metals() -> List[Instrument]:
    spot = [("XAUUSD", "gold"), ("XAGUSD", "silver"), ("XPTUSD", "platinum"), ("XPDUSD", "palladium")]
    fut = [("GC=F", "gold futures"), ("SI=F", "silver futures"), ("PL=F", "platinum futures"),
           ("PA=F", "palladium futures"), ("HG=F", "copper futures")]
    out = [Instrument(s, s + "=X" if "=X" not in s and "=" not in s else s, n, "metal",
                      "global", has_volume="=" in s) for s, n in spot]
    out += [Instrument(s.replace("=", "").replace("F", "") + "FUT", s, n, "metal", "global",
                       has_volume=True) for s, n in fut]
    return out


def _energy() -> List[Instrument]:
    rows = [("CL=F", "wti crude"), ("BZ=F", "brent crude"), ("NG=F", "natural gas"),
            ("RB=F", "rbob gasoline"), ("HO=F", "heating oil")]
    return [Instrument(s.split("=")[0] + "FUT", s, n, "energy", "global", has_volume=True)
            for s, n in rows]


def _agri() -> List[Instrument]:
    rows = [("ZW=F", "wheat srx"), ("KE=F", "wheat kc"), ("ZC=F", "corn"), ("ZS=F", "soybeans"),
            ("ZM=F", "soybean meal"), ("ZL=F", "soybean oil"), ("KC=F", "coffee arabica"),
            ("CC=F", "cocoa"), ("SB=F", "sugar"), ("CT=F", "cotton"), ("OJ=F", "orange juice"),
            ("LE=F", "live cattle"), ("HE=F", "lean hogs"), ("LBS=F", "lumber"),
            ("RR=F", "rice")]
    return [Instrument(s.split("=")[0] + "FUT", s, n, "agri", "global", has_volume=True)
            for s, n in rows]


def _indices() -> List[Instrument]:
    rows = [("^GSPC", "S&P 500", "us"), ("^NDX", "Nasdaq 100", "us"), ("^DJI", "Dow Jones", "us"),
            ("^RUT", "Russell 2000", "us"), ("^VIX", "VIX", "us"),
            ("^GDAXI", "DAX", "de"), ("^FTSE", "FTSE 100", "uk"), ("^FCHI", "CAC 40", "fr"),
            ("^STOXX50E", "Euro Stoxx 50", "eu"), ("^IBEX", "IBEX 35", "es"),
            ("^SSMI", "Swiss Market", "ch"), ("^AEX", "AEX", "nl"), ("^BFX", "BEL 20", "be"),
            ("^OMX", "OMX Stockholm 30", "se"), ("^N225", "Nikkei 225", "jp"),
            ("^HSI", "Hang Seng", "hk"), ("^KS11", "KOSPI", "kr"), ("^TWII", "Taiwan Weighted", "tw"),
            ("^AXJO", "ASX 200", "au"), ("^BSESN", "BSE Sensex", "in"), ("^NSEI", "Nifty 50", "in"),
            ("^STI", "Straits Times", "sg"), ("^JKSE", "Jakarta Composite", "id"),
            ("^KLSE", "FTSE Malaysia", "my"), ("^SET.BK", "SET 50", "th"),
            ("^BVSP", "Bovespa", "br"), ("^MXX", "IPC Mexico", "mx"),
            ("^MERV", "Merval", "ar"), ("^TA125.TA", "TA-125", "il")]
    return [Instrument(s.strip("^").replace(".", ""), s, n, "index", r) for s, n, r in rows]


def _crypto() -> List[Instrument]:
    rows = ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "LINK", "DOT",
            "TON", "TRX", "LTC", "BCH", "XMR"]
    return [Instrument(c + "USD", c + "-USD", c + "/USD", "crypto", "global",
                       has_volume=True, session="24x7") for c in rows]


def _etf_bond() -> List[Instrument]:
    etf = [("SPY", "S&P 500 ETF", "etf"), ("QQQ", "Nasdaq 100 ETF", "etf"),
           ("IWM", "Russell 2000 ETF", "etf"), ("EEM", "EM equity ETF", "etf"),
           ("GLD", "gold ETF", "etf"), ("SLV", "silver ETF", "etf"), ("USO", "oil ETF", "etf"),
           ("DBC", "commodity ETF", "etf"), ("VNQ", "REIT ETF", "etf"),
           ("TLT", "20y treasury ETF", "bond"), ("IEF", "7-10y treasury ETF", "bond"),
           ("SHY", "1-3y treasury ETF", "bond"), ("LQD", "IG credit ETF", "bond"),
           ("HYG", "high yield credit ETF", "bond"), ("EMB", "EM debt ETF", "bond")]
    return [Instrument(s, s, n, k, "us", has_volume=True) for s, n, k in etf]


def _equity_seed() -> List[Instrument]:
    rows = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", "JPM", "XOM"]
    return [Instrument(s.replace("-", ""), s, s, "equity", "us", has_volume=True) for s in rows]


UNIVERSE: List[Instrument] = (_fx() + _metals() + _energy() + _agri()
                              + _indices() + _crypto() + _etf_bond() + _equity_seed())


def universe(asset_class: Optional[str] = None, region: Optional[str] = None) -> List[Instrument]:
    out = UNIVERSE
    if asset_class:
        out = [i for i in out if i.asset_class == asset_class]
    if region:
        out = [i for i in out if i.region == region]
    return list(out)


def by_class() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i in UNIVERSE:
        out[i.asset_class] = out.get(i.asset_class, 0) + 1
    return out


def get(symbol: str) -> Instrument:
    for i in UNIVERSE:
        if i.symbol == symbol:
            return i
    raise KeyError(symbol)


def load_listing(path: str | Path, asset_class: str) -> List[Instrument]:
    """Full market listing from a vendor CSV: symbol,name,exchange,region,currency[,yahoo]."""
    out: List[Instrument] = []
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for n, row in enumerate(csv.DictReader(fh), start=2):
            try:
                out.append(Instrument(
                    symbol=row["symbol"].strip(),
                    yahoo=(row.get("yahoo") or row["symbol"]).strip(),
                    name=row.get("name", row["symbol"]).strip(),
                    asset_class=asset_class,
                    region=(row.get("region") or row.get("exchange") or "unknown").strip(),
                    currency=(row.get("currency") or "USD").strip(),
                    has_volume=True,
                ))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"{path}:{n}: {exc}") from exc
    return out
