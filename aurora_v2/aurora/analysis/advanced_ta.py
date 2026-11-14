"""Advanced technical analysis built from things that can be measured, not folklore.

The requirement was "all the world's technical analysis". Most of what is sold under that
name is unfalsifiable: smart money concepts, order blocks and liquidity sweeps cannot be
defined precisely enough to test, so a system that uses them can never be wrong and can
never be improved either. What is here instead is the subset that can be written down as a
function, measured on history, and inspected by a user who disagrees:

  swing structure   higher highs and higher lows, computed, not narrated
  Donchian range    the breakout definition that already exists in the cross-asset sleeve
  ATR               volatility in price units, the honest denominator for stop distance
  RSI               the one oscillator in the standard canon that is fully defined
  volume profile    where volume actually traded: point of control and value area

Two rules from the project's own history:
  - Nothing here enters the recommendation SCORE. The factor weights in
    aurora/advisory/recommender.py were pre-registered; a new ingredient gets weighted only
    after a walk-forward shows it adds something. Until then it is a REPORT layer, so the
    user sees the structure while the ranking stays honest.
  - A read with too little data says so instead of returning a neutral-looking zero.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

RISE = "صعودی"
FALL = "نزولی"
RANGE = "خنثی/رنج"
BREAK_UP = "شکست صعودی"
BREAK_DOWN = "شکست نزولی"
INSIDE = "داخل دامنه"


@dataclass(frozen=True)
class Swing:
    index: int
    price: float
    kind: str          # "high" or "low"


@dataclass
class TechnicalRead:
    symbol: str
    structure: str
    breakout: str
    atr_pct: Optional[float]
    rsi_value: Optional[float]
    poc: Optional[float]
    value_area: Optional[Tuple[float, float]]
    price_vs_poc_pct: Optional[float]
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def line(self) -> str:
        bits = [f"ساختار {self.structure}", f"دامنه: {self.breakout}"]
        if self.atr_pct is not None:
            bits.append(f"ATR {self.atr_pct:.2f}%")
        if self.rsi_value is not None:
            bits.append(f"RSI {self.rsi_value:.0f}")
        if self.price_vs_poc_pct is not None:
            bits.append(f"{self.price_vs_poc_pct:+.1f}% نسبت به POC")
        return f"{self.symbol}: " + "، ".join(bits)


# ---------------------------------------------------------------- structure
def swing_points(values: Sequence[float], k: int = 2) -> List[Swing]:
    """Local extrema that are extrema against k bars on BOTH sides.

    This is the definition most 'market structure' teaching gestures at but never states:
    a swing high exists only in hindsight, which is exactly why the code must exclude the
    last k bars when deciding - otherwise the same bar changes the verdict as data arrives.
    """
    if k < 1:
        raise ValueError("k باید حداقل ۱ باشد")
    out: List[Swing] = []
    for i in range(k, len(values) - k):
        window = values[i - k:i + k + 1]
        if values[i] == max(window) and window.count(values[i]) == 1:
            out.append(Swing(i, values[i], "high"))
        elif values[i] == min(window) and window.count(values[i]) == 1:
            out.append(Swing(i, values[i], "low"))
    return out


def trend_structure(swings: Sequence[Swing]) -> str:
    """Higher highs AND higher lows is an uptrend; lower/lower is a downtrend; else range."""
    highs = [s.price for s in swings if s.kind == "high"]
    lows = [s.price for s in swings if s.kind == "low"]
    if len(highs) < 2 or len(lows) < 2:
        return RANGE
    rising = highs[-1] > highs[-2] and lows[-1] > lows[-2]
    falling = highs[-1] < highs[-2] and lows[-1] < lows[-2]
    if rising:
        return RISE
    if falling:
        return FALL
    return RANGE


def donchian(values: Sequence[float], lookback: int = 55) -> Tuple[float, float]:
    if len(values) < lookback:
        raise ValueError(f"برای دامنه {lookback} روزه داده کافی نیست")
    window = values[-lookback:]
    return max(window), min(window)


def range_breakout(values: Sequence[float], lookback: int = 55) -> str:
    """Comparisons use the channel formed BEFORE the latest bar, so today cannot define
    its own breakout level and then break it."""
    if len(values) < lookback + 1:
        return INSIDE
    upper, lower = donchian(values[:-1], lookback)
    last = values[-1]
    if last > upper:
        return BREAK_UP
    if last < lower:
        return BREAK_DOWN
    return INSIDE


# ---------------------------------------------------------------- volatility
def true_ranges(highs: Sequence[float], lows: Sequence[float],
                closes: Sequence[float]) -> List[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("سری‌های قیمت باید هم‌طول باشند")
    out: List[float] = []
    for i in range(1, len(closes)):
        out.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    return out


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
        n: int = 14) -> Optional[float]:
    trs = true_ranges(highs, lows, closes)
    if len(trs) < n:
        return None
    return sum(trs[-n:]) / n


def atr_pct(highs, lows, closes, n: int = 14) -> Optional[float]:
    value = atr(highs, lows, closes, n)
    if value is None or not closes or closes[-1] <= 0:
        return None
    return value / closes[-1] * 100.0


# ---------------------------------------------------------------- momentum
def rsi(closes: Sequence[float], n: int = 14) -> Optional[float]:
    """Wilder's RSI, written out so the boundary cases (no losses, no gains) are explicit."""
    if len(closes) < n + 1:
        return None
    gains, losses = 0.0, 0.0
    for i in range(len(closes) - n, len(closes)):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            gains += delta
        else:
            losses -= delta
    if gains == 0 and losses == 0:
        return 50.0                      # a flat series is neutral, not undefined
    if losses == 0:
        return 100.0
    rs = (gains / n) / (losses / n)
    return 100.0 - 100.0 / (1.0 + rs)


# ---------------------------------------------------------------- volume
def volume_profile(closes: Sequence[float], volumes: Sequence[float],
                   bins: int = 24, value_area: float = 0.70) -> Dict[str, object]:
    """Where volume traded: point of control plus the 70% value area around it.

    Bin edges come from the price range, so the result is a description of THIS window and
    is not comparable across windows - which is why the read reports percentages relative
    to the POC rather than raw levels.
    """
    if len(closes) != len(volumes):
        raise ValueError("قیمت و حجم باید هم‌طول باشند")
    if len(closes) < bins or bins < 2:
        return {"poc": None, "value_area": None, "bins": bins, "used": len(closes)}
    lo, hi = min(closes), max(closes)
    if hi <= lo:
        return {"poc": lo, "value_area": (lo, hi), "bins": bins, "used": len(closes)}
    width = (hi - lo) / bins
    buckets = [0.0] * bins
    for price, volume in zip(closes, volumes):
        idx = min(bins - 1, int((price - lo) / width))
        buckets[idx] += volume
    poc_idx = max(range(bins), key=lambda i: buckets[i])
    poc = lo + (poc_idx + 0.5) * width

    total = sum(buckets) or 1.0
    taken = buckets[poc_idx]
    low_i = high_i = poc_idx
    while taken / total < value_area and (low_i > 0 or high_i < bins - 1):
        below = buckets[low_i - 1] if low_i > 0 else -1.0
        above = buckets[high_i + 1] if high_i < bins - 1 else -1.0
        if above >= below:
            high_i += 1
            taken += buckets[high_i]
        else:
            low_i -= 1
            taken += buckets[low_i]
    return {"poc": poc, "value_area": (lo + low_i * width, lo + (high_i + 1) * width),
            "bins": bins, "used": len(closes), "coverage": taken / total}


# ---------------------------------------------------------------- the read
def technical_read(symbol: str, bars: Sequence, k: int = 2, lookback: int = 55,
                   rsi_n: int = 14, profile_window: int = 252) -> TechnicalRead:
    """One instrument's structural picture, with every limitation stated."""
    if not bars:
        return TechnicalRead(symbol, RANGE, INSIDE, None, None, None, None, None,
                             warnings=["هیچ کندلی برای تحلیل نبود"])
    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    volumes = [getattr(b, "volume", 0.0) or 0.0 for b in bars]

    warnings: List[str] = []
    reasons: List[str] = []

    structure = trend_structure(swing_points(closes, k))
    breakout = range_breakout(closes, lookback)
    if len(closes) < lookback + 1:
        warnings.append(f"تاریخچه کمتر از {lookback + 1} کندل: دامنه محاسبه نشد")
    if len(closes) < 30:
        warnings.append("تاریخچه کوتاه: ساختار سوئینگ قابل اتکا نیست")

    ap = atr_pct(highs, lows, closes)
    rs = rsi(closes, rsi_n)
    if ap is None:
        warnings.append("ATR محاسبه نشد (کندل کافی نبود)")
    if rs is None:
        warnings.append("RSI محاسبه نشد (کندل کافی نبود)")

    # the profile window matters: on a 20-year series the point of control sits at a 2006
    # price and the percentage vs today is meaningless. One trading year is the window.
    recent = slice(max(0, len(closes) - profile_window), len(closes))
    vp = volume_profile(closes[recent], volumes[recent])
    poc = vp.get("poc")
    area = vp.get("value_area")
    vs_poc = None
    if poc:
        vs_poc = (closes[-1] / poc - 1.0) * 100.0
        reasons.append(f"قیمت {vs_poc:+.1f}% نسبت به نقطه کنترل حجم "
                       f"(پنجره {min(profile_window, len(closes))} کندل)")
    else:
        warnings.append("پروفایل حجم محاسبه نشد (حجم یا تعداد کندل کافی نبود)")

    reasons.append(f"ساختار سوئینگ: {structure}")
    reasons.append(f"دامنه {lookback} روزه: {breakout}")
    if ap is not None:
        reasons.append(f"نوسان ATR {ap:.2f}% از قیمت؛ فاصله حد ضرر باید از این بزرگ‌تر باشد")
    if rs is not None:
        tag = "اشباع خرید" if rs >= 70 else "اشباع فروش" if rs <= 30 else "میانه"
        reasons.append(f"RSI {rs:.0f} ({tag})")

    # contradictions are reported as contradictions, not smoothed into a verdict
    if structure == RISE and breakout == BREAK_DOWN:
        warnings.append("تضاد: ساختار صعودی ولی شکست نزولی دامنه")
    if rs is not None and rs >= 70 and breakout == BREAK_UP:
        warnings.append("شکست صعودی در اشباع خرید: ریسک بازگشت به میانگین")

    return TechnicalRead(symbol, structure, breakout, ap, rs, poc, area, vs_poc,
                         reasons, warnings)


def confirmation(read: TechnicalRead) -> str:
    """A three-state confirmation for the advisory report. No score, no weight, no claim."""
    if read.warnings and any("تضاد" in w for w in read.warnings):
        return "متناقض"
    if read.structure == RISE and read.breakout in (BREAK_UP, INSIDE):
        return "هم‌جهت با روند"
    if read.structure == FALL and read.breakout == BREAK_DOWN:
        return "هم‌جهت با روند نزولی"
    return "بدون تأیید"
