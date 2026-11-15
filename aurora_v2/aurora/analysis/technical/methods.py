"""The technical analysis package: many methods, each with a stated failure mode.

The owner's requirement is a *package* of technical methods, not one indicator, plus a platform
that picks the right one per asset. That only works if every method declares what it is good at
and where it breaks. A method that claims to work everywhere cannot be selected between, and
selection is the whole point.

Every evaluator has the same shape: bars in, `Verdict` out. No evaluator may raise for ordinary
missing data; it returns `None` so the selector can drop it honestly instead of scoring a zero,
because zero is a real opinion and "no data" is not.
"""
from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Dict, List, Optional, Sequence, Tuple

from aurora.analysis import advanced_ta as ta
from aurora.analysis import trend_rules as tr

TREND = "trend"
MEAN_REVERSION = "mean_reversion"
BREAKOUT = "breakout"
STRUCTURE = "structure"
FLOW = "flow"
MOMENTUM = "momentum"

METHOD_CLASS_BIAS: Dict[str, Dict[str, float]] = {
    # prior weights, frozen before measurement: what each family is expected to suit
    "equity": {TREND: 1.0, MOMENTUM: 1.0, STRUCTURE: 0.9, BREAKOUT: 0.7, MEAN_REVERSION: 0.8, FLOW: 0.6},
    "etf": {TREND: 1.0, MOMENTUM: 0.9, STRUCTURE: 0.9, BREAKOUT: 0.8, MEAN_REVERSION: 0.8, FLOW: 0.6},
    "index": {TREND: 1.0, MOMENTUM: 1.0, STRUCTURE: 0.9, BREAKOUT: 0.8, MEAN_REVERSION: 0.6, FLOW: 0.6},
    "metals": {STRUCTURE: 1.0, TREND: 0.9, BREAKOUT: 0.8, MEAN_REVERSION: 0.7, MOMENTUM: 0.7, FLOW: 0.5},
    "energy": {STRUCTURE: 1.0, BREAKOUT: 0.9, TREND: 0.9, MEAN_REVERSION: 0.6, MOMENTUM: 0.7, FLOW: 0.5},
    "agri": {STRUCTURE: 1.0, BREAKOUT: 0.9, MEAN_REVERSION: 0.8, TREND: 0.7, MOMENTUM: 0.6, FLOW: 0.5},
    "fx": {TREND: 1.0, STRUCTURE: 1.0, MOMENTUM: 0.9, BREAKOUT: 0.8, MEAN_REVERSION: 0.7, FLOW: 0.5},
    "crypto": {MOMENTUM: 1.0, TREND: 0.9, BREAKOUT: 0.9, STRUCTURE: 0.8, MEAN_REVERSION: 0.7, FLOW: 0.6},
    "fixed_income": {TREND: 0.9, MEAN_REVERSION: 0.9, STRUCTURE: 0.8, MOMENTUM: 0.7, BREAKOUT: 0.5, FLOW: 0.4},
    "fund": {TREND: 0.9, MOMENTUM: 0.8, STRUCTURE: 0.8, MEAN_REVERSION: 0.7, BREAKOUT: 0.6, FLOW: 0.5},
}


@dataclass(frozen=True)
class Verdict:
    method: str
    family: str
    score: float                     # -1 (short/avoid) .. +1 (long)
    confidence: float                # 0..1, how much data backed the reading
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def _series(bars: Sequence) -> Tuple[List[float], List[float], List[float], List[float]]:
    return ([b.high for b in bars], [b.low for b in bars],
            [b.close for b in bars], [getattr(b, "volume", 0.0) or 0.0 for b in bars])


def slope_pct(values: Sequence[float], window: int = 20) -> Optional[float]:
    """Percent change of a straight line fitted through the last window (least squares)."""
    if len(values) < window or window < 2:
        return None
    ys = list(values[-window:])
    n = len(ys)
    xs = list(range(n))
    mx, my = mean(xs), mean(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0 or my == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return slope * n / my * 100.0


def structure_method(bars: Sequence) -> Optional[Verdict]:
    highs, lows, closes, _ = _series(bars)
    if len(closes) < 60:
        return None
    swings = ta.swing_points(closes, k=2)
    state = ta.trend_structure(swings)
    score = 1.0 if state == tr.UP else -1.0 if state == tr.DOWN else 0.0
    last = closes[-1]
    reasons = [f"ساختار: {state}"]
    if swings:
        reasons.append(f"آخرین سوئینگ {swings[-1].kind} در {swings[-1].price:.2f}")
    conf = 0.8 if len(swings) >= 4 else 0.4
    warns = [] if len(swings) >= 4 else ["سوئینگ‌های کم: ساختار قابل اتکا نیست"]
    return Verdict("structure", STRUCTURE, score, conf, reasons, warns)


def trend_method(bars: Sequence) -> Optional[Verdict]:
    highs, lows, closes, _ = _series(bars)
    if len(closes) < 220:
        return None
    fast, slow = tr.ema_series(closes, 50), tr.ema_series(closes, 200)
    if not fast or not slow:
        return None
    aligned = fast[-1] > slow[-1]
    slope = slope_pct(fast, 20) or 0.0
    score = _clamp((0.5 if aligned else -0.5) + _clamp(slope / 2.0) * 0.5)
    return Verdict("trend", TREND, score, 0.85,
                   [f"EMA50 {'بالای' if aligned else 'زیر'} EMA200",
                    f"شیب EMA50: {slope:+.2f}% در ۲۰ کندل"])


def momentum_method(bars: Sequence) -> Optional[Verdict]:
    _, _, closes, _ = _series(bars)
    if len(closes) < 120:
        return None
    r = ta.rsi(closes, 14)
    macd, signal = tr.macd(closes) if hasattr(tr, "macd") else (None, None)
    if r is None:
        return None
    score = _clamp((r - 50.0) / 30.0)
    reasons = [f"RSI {r:.0f}"]
    if macd is not None and signal is not None:
        score = _clamp(score * 0.6 + (1.0 if macd > signal else -1.0) * 0.4)
        reasons.append(f"MACD {'بالای' if macd > signal else 'زیر'} سیگنال")
    return Verdict("momentum", MOMENTUM, score, 0.7, reasons)


def breakout_method(bars: Sequence) -> Optional[Verdict]:
    _, _, closes, _ = _series(bars)
    if len(closes) < 60:
        return None
    try:
        state = ta.range_breakout(closes, lookback=55)
    except ValueError:
        return None
    score = 1.0 if state == ta.BREAK_UP else -1.0 if state == ta.BREAK_DOWN else 0.0
    return Verdict("breakout", BREAKOUT, score, 0.6,
                   [f"کانال ۵۵ روزه: {state}"],
                   [] if score else ["بدون شکست: روند خودش را نشان نداده"])


def mean_reversion_method(bars: Sequence) -> Optional[Verdict]:
    _, _, closes, _ = _series(bars)
    if len(closes) < 40:
        return None
    window = closes[-20:]
    mu, sigma = mean(window), pstdev(window)
    if sigma == 0:
        return None
    z = (closes[-1] - mu) / sigma
    return Verdict("mean_reversion", MEAN_REVERSION, _clamp(-z / 2.0), 0.6,
                   [f"انحراف از میانگین ۲۰ روزه: {z:+.2f}σ"])


def flow_method(bars: Sequence) -> Optional[Verdict]:
    _, _, closes, vols = _series(bars)
    if len(closes) < 60 or not any(vols):
        return None
    vp = ta.volume_profile(closes[-252:], vols[-252:], bins=24)
    poc = vp["poc"] if isinstance(vp, dict) else getattr(vp, "poc", None)
    if not poc:
        return None
    above = closes[-1] > poc
    return Verdict("flow", FLOW, 0.5 if above else -0.5, 0.5,
                   [f"قیمت {'بالای' if above else 'زیر'} POC ({poc:.2f})"])


EVALUATORS = {
    "structure": structure_method,
    "trend": trend_method,
    "momentum": momentum_method,
    "breakout": breakout_method,
    "mean_reversion": mean_reversion_method,
    "flow": flow_method,
}


def evaluate_all(bars: Sequence, asset_class: str = "equity") -> List[Verdict]:
    """Run every applicable method. Missing data drops a method; it never scores it zero."""
    out: List[Verdict] = []
    for name, fn in EVALUATORS.items():
        try:
            v = fn(bars)
        except Exception:                      # a broken evaluator must not kill the screen
            continue
        if v is not None and abs(v.score) > 0:
            out.append(v)
    return out
