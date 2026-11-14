"""TSETMC symbol resolution: Persian names compare unequal for invisible reasons.

Arabic yeh and Persian yeh are different code points that render identically, and
the same is true of kaf/keheh. A folder of CSVs downloaded from TSETMC mixes both
plus zero-width non-joiners, so an exact dictionary lookup silently misses and a
researcher concludes the symbol does not exist. Normalising first is not cosmetic;
it is the difference between a match and a false absence.
"""
import difflib
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional

_AR_TO_FA = {
    "\u064a": "\u06cc",   # Arabic yeh -> Persian yeh
    "\u0649": "\u06cc",   # alef maksura -> Persian yeh
    "\u0643": "\u06a9",   # Arabic kaf -> Persian keheh
    "\u0629": "\u0647",   # teh marbuta -> heh
    "\u200c": " ",        # zero-width non-joiner
    "\u200f": " ",        # right-to-left mark
    "\u200e": " ",
    "\u0640": "",         # tatweel
}
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_persian(text: str) -> str:
    """Collapse the spellings that look identical on screen into one key."""
    if text is None:
        return ""
    out = unicodedata.normalize("NFKC", str(text))
    for src, dst in _AR_TO_FA.items():
        out = out.replace(src, dst)
    out = out.translate(_DIGITS)
    out = re.sub(r"[\u064b-\u0652]", "", out)      # harakat
    out = re.sub(r"\s+", " ", out).strip()
    return out


class TsetmcSymbolError(KeyError):
    """Raised when a symbol cannot be resolved, carrying close candidates."""

    def __init__(self, query: str, candidates: Iterable[str]):
        self.query = query
        self.candidates = list(candidates)
        hint = f"; did you mean: {', '.join(self.candidates)}" if self.candidates else ""
        super().__init__(f"unknown TSETMC symbol {query!r}{hint}")


def load_tsetmc_listing(path: str | Path) -> Dict[str, Dict[str, str]]:
    """Read a TSETMC instrument list: columns isin, ticker, name (any order)."""
    import csv

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    out: Dict[str, Dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            clean = {normalize_persian(k).lower(): (v or "").strip() for k, v in row.items() if k}
            isin = clean.get("isin") or clean.get("کد isin") or ""
            ticker = clean.get("ticker") or clean.get("نماد") or clean.get("symbol") or ""
            name = clean.get("name") or clean.get("نام") or clean.get("نام شرکت") or ""
            if not (isin or ticker or name):
                continue
            key = isin or ticker or normalize_persian(name)
            out[key] = {"isin": isin, "ticker": ticker, "name": name}
    if not out:
        raise ValueError(f"{path.name}: no instruments found")
    return out


def resolve_tsetmc(query: str, listing: Dict[str, Dict[str, str]], cutoff: float = 0.84):
    """Match on ISIN, then ticker, then normalised name; suggest when nothing fits."""
    q = normalize_persian(query)
    if not q:
        raise TsetmcSymbolError(query, [])
    if q in listing:
        return listing[q]
    ql = q.lower()
    for key, row in listing.items():
        if key.lower() == ql:
            return row
    for row in listing.values():
        if ql in (normalize_persian(row["ticker"]).lower(), normalize_persian(row["isin"]).lower()):
            return row
    names = {normalize_persian(row["name"]): row for row in listing.values() if row["name"]}
    if q in names:
        return names[q]
    # a substring hit is a suggestion, never an automatic answer: "فولاد" appears
    # in dozens of listed names and guessing which one was meant is how a backtest
    # silently trades the wrong company
    inside = [n for n in names if q in n]
    if inside:
        raise TsetmcSymbolError(query, inside[:3])
    close = difflib.get_close_matches(q, list(names), n=3, cutoff=cutoff)
    raise TsetmcSymbolError(query, close)
