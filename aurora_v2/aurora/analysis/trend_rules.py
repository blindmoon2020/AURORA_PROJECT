"""The owner's trend-and-pullback rulebook, written as rules that can pass or fail.

The methodology arrived as prose: structure first, EMA 50/200 second, RSI above or below 50 as
confirmation, entries only on a pullback (resistance flip, dynamic MA support, continuation
break), stop behind the last valid swing, reward:risk at least 1:2. Prose cannot be tested, so
every clause becomes a numbered condition and each function returns a verdict with its reasons.

Three deliberate choices, each of which costs something:

1. Structure is the FIRST filter, not the EMA. Teaching that lists structure first often then
   trades EMA crosses; when they disagree the EMA is the weaker evidence (a smoothed price, not
   a market event), so disagreement produces "range", never an entry.
2. A pin bar or engulfing candle is defined by ratios (body/range, wick share), because "looks
   like a pin" is not a rule and cannot be reproduced by someone else.
3. The stop sits behind the swing with an ATR buffer and the target is a fixed R multiple, so
   neither is fitted to what happened next.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from aurora.analysis.advanced_ta import atr, rsi, swing_points, trend_structure

UP, DOWN, RANGE = "صعودی", "نزولی", "رنج"
LONG, SHORT, NONE = "خرید", "فروش", "بدون ورود"

MIN_BARS = 220          # EMA200 needs a real sample before it means anything
ATR_BUFFER = 0.25       # the stop sits this many ATR beyond the swing, not exactly on it
MIN_RR = 2.0            # the owner's own floor: 1:2 or better
AGREE_THRESHOLD = 80.0  # percent of weighted votes needed to call a trend


def ema(values: Sequence[float], n: int) -> Optional[float]:
    """Exponential average seeded with the SMA of the first n values.

    A raw EMA from bar 0 carries the first price far longer than anyone expects. Seeding with
    the SMA is the convention charting platforms use, so the number here matches the number the
    owner sees on his own chart instead of almost matching it.
    """
    if n <= 0 or len(values) < n:
        return None
    k = 2.0 / (n + 1.0)
    value = sum(values[:n]) / n
    for price in values[n:]:
        value = price * k + value * (1.0 - k)
    return value


def ema_series(values: Sequence[float], n: int) -> List[float]:
    if n <= 0 or len(values) < n:
        return []
    k = 2.0 / (n + 1.0)
    out = [sum(values[:n]) / n]
    for price in values[n:]:
        out.append(price * k + out[-1] * (1.0 - k))
    return out


def slope_pct(series: Sequence[float], lookback: int = 10) -> Optional[float]:
    """Percent change across the last `lookback` bars of the series itself (not of price)."""
    if len(series) < lookback + 1 or series[-lookback - 1] == 0:
        return None
    return (series[-1] / series[-lookback - 1] - 1.0) * 100.0


@dataclass
class TrendRead:
    state: str
    score: float
    structure: str
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    rsi_value: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def line(self) -> str:
        bits = [f"وضعیت: {self.state} (امتیاز {self.score:.0f}٪)", f"ساختار: {self.structure}"]
        if self.rsi_value is not None:
            bits.append(f"RSI {self.rsi_value:.0f}")
        return " · ".join(bits)


def detect_trend(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
                 k: int = 2) -> TrendRead:
    """The three filters in the owner's order; disagreement means no trade, not a vote."""
    if len(closes) < MIN_BARS:
        return TrendRead(RANGE, 0.0, "داده ناکافی", warnings=[
            f"حداقل {MIN_BARS} کندل لازم است؛ {len(closes)} کندل موجود است"])

    structure = trend_structure(swing_points(closes, k=k))
    fast, slow = ema(closes, 50), ema(closes, 200)
    fast_slope = slope_pct(ema_series(closes, 50)) if len(closes) >= 60 else None
    momentum = rsi(closes)

    votes_up = votes_down = 0
    total = 0
    reasons: List[str] = []

    total += 2
    if structure == "صعودی":
        votes_up += 2
    elif structure == "نزولی":
        votes_down += 2
    reasons.append(f"ساختار سوئینگ: {structure}")

    if fast is not None and slow is not None:
        total += 2
        if fast > slow and (fast_slope or 0.0) > 0:
            votes_up += 2
            reasons.append("EMA50 بالای EMA200 با شیب مثبت")
        elif fast < slow and (fast_slope or 0.0) < 0:
            votes_down += 2
            reasons.append("EMA50 زیر EMA200 با شیب منفی")
        else:
            reasons.append("میانگین‌ها هم‌جهت نیستند")

    if momentum is not None:
        total += 1
        if momentum > 50:
            votes_up += 1
            reasons.append(f"RSI {momentum:.0f} بالای ۵۰")
        elif momentum < 50:
            votes_down += 1
            reasons.append(f"RSI {momentum:.0f} زیر ۵۰")

    score_up = votes_up / total * 100.0
    score_down = votes_down / total * 100.0
    if score_up >= AGREE_THRESHOLD:
        state = UP
    elif score_down >= AGREE_THRESHOLD:
        state = DOWN
    else:
        state = RANGE
        if max(score_up, score_down) >= 40.0:
            reasons.append("فیلترها هم‌جهت نیستند؛ طبق قاعده معامله انجام نمی‌شود")
    return TrendRead(state, max(score_up, score_down), structure, fast, slow, momentum, reasons)


def is_pin_bar(open_: float, high: float, low: float, close: float,
               body_max: float = 0.35, wick_min: float = 0.55) -> Optional[str]:
    """A pin is a small body at one end of a long range, by ratio rather than by eye."""
    rng = high - low
    if rng <= 0:
        return None
    if abs(close - open_) / rng > body_max:
        return None
    upper = high - max(open_, close)
    lower = min(open_, close) - low
    if lower / rng >= wick_min:
        return "پین صعودی"
    if upper / rng >= wick_min:
        return "پین نزولی"
    return None


def is_engulfing(prev: Tuple[float, float], now: Tuple[float, float]) -> Optional[str]:
    """The current body swallows the previous body, in the opposite direction."""
    p_open, p_close = prev
    c_open, c_close = now
    if p_close <= p_open and c_close > c_open and c_close >= p_open and c_open <= p_close:
        return "پوشای صعودی"
    if p_close >= p_open and c_close < c_open and c_close <= p_open and c_open >= p_close:
        return "پوشای نزولی"
    return None


@dataclass
class EntryPlan:
    action: str
    entry: Optional[float] = None
    stop: Optional[float] = None
    target: Optional[float] = None
    rr: Optional[float] = None
    trigger: str = ""
    reasons: List[str] = field(default_factory=list)

    def line(self) -> str:
        if self.action == NONE or self.entry is None:
            return "بدون ورود · " + ("؛ ".join(self.reasons) or "شرط‌ها کامل نیست")
        return (f"{self.action} · ورود {self.entry:.4f} · حد ضرر {self.stop:.4f} · "
                f"هدف {self.target:.4f} · R:R {self.rr:.2f} · {self.trigger}")


def last_swing(highs: Sequence[float], lows: Sequence[float], k: int = 2,
               kind: str = "low") -> Optional[float]:
    points = swing_points(lows if kind == "low" else highs, k=k)
    return points[-1].price if points else None


def plan_entry(highs: Sequence[float], lows: Sequence[float], opens: Sequence[float],
               closes: Sequence[float], rr_target: float = MIN_RR) -> EntryPlan:
    """Trend first, then a pullback trigger, then a stop behind the swing. Never the reverse.

    An entry trigger without a trend is a coin flip with a story; a stop placed before the
    direction is decided is a position looking for a reason.
    """
    trend = detect_trend(highs, lows, closes)
    if trend.state == RANGE:
        return EntryPlan(NONE, reasons=["روند هم‌جهت نیست؛ طبق قاعده ورود ممنوع"] + trend.reasons[:2])

    price = closes[-1]
    atr_value = atr(highs, lows, closes) or 0.0
    fast = trend.ema_fast
    candle = is_pin_bar(opens[-1], highs[-1], lows[-1], closes[-1]) or \
        is_engulfing((opens[-2], closes[-2]), (opens[-1], closes[-1]))

    if trend.state == UP:
        near_fast = fast is not None and price <= fast * 1.015
        if not (candle and near_fast):
            return EntryPlan(NONE, reasons=["روند صعودی است ولی تریگر پولبک دیده نشد"])
        swing = last_swing(highs, lows, kind="low")
        if swing is None:
            return EntryPlan(NONE, reasons=["کف معتبری برای حد ضرر پیدا نشد"])
        stop = swing - ATR_BUFFER * atr_value
        risk = price - stop
        if risk <= 0:
            return EntryPlan(NONE, reasons=["فاصله حد ضرر نامعتبر است"])
        target, action = price + rr_target * risk, LONG
    else:
        near_fast = fast is not None and price >= fast * 0.985
        if not (candle and near_fast):
            return EntryPlan(NONE, reasons=["روند نزولی است ولی تریگر پولبک دیده نشد"])
        swing = last_swing(highs, lows, kind="high")
        if swing is None:
            return EntryPlan(NONE, reasons=["سقف معتبری برای حد ضرر پیدا نشد"])
        stop = swing + ATR_BUFFER * atr_value
        risk = stop - price
        if risk <= 0:
            return EntryPlan(NONE, reasons=["فاصله حد ضرر نامعتبر است"])
        target, action = price - rr_target * risk, SHORT

    rr = abs(target - price) / abs(price - stop)
    if rr + 1e-9 < MIN_RR:
        return EntryPlan(NONE, reasons=[f"R:R {rr:.2f} کمتر از کف {MIN_RR:.1f}"])
    return EntryPlan(action, price, stop, target, rr, f"پولبک به EMA50 + {candle}",
                     [f"روند {trend.state}", f"R:R {rr:.2f}"])


def position_size(equity: float, risk_pct: float, entry: float, stop: float) -> float:
    """Units such that a stop-out costs exactly risk_pct of equity, and never more."""
    per_unit = abs(entry - stop)
    if per_unit <= 0 or equity <= 0 or risk_pct <= 0:
        return 0.0
    return (equity * risk_pct / 100.0) / per_unit
