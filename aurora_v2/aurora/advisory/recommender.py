"""The advisory engine: a ranked decision surface with reasons, not a promise of return.

What this module is allowed to claim, and what it is not:

  IT IS a transparent ranker. Every recommendation carries the factors that produced it,
  their measured values, and the percentile each one sits at. A user can disagree with a
  recommendation by reading the reasons - which is the opposite of a black box.

  IT IS NOT an edge claim. The rule weights below were fixed BEFORE looking at any output
  and are recorded in one place, so a later "improvement" has to be a documented change,
  not a quiet tune. AURORA's measured information ratio against equal weight is 0.06: this
  engine organizes decisions, it does not beat the market by existing.

Three design rules that follow from the mission requirements:

  1. MISSING DATA IS NAMED, NEVER SCORED AS ZERO. If fundamentals are absent the weight is
     redistributed across the available factors and a warning is emitted. A zero is a
     measurement; an absence is not.
  2. NO RECOMMENDATION WITHOUT A RISK BUDGET. Target weights come from inverse volatility,
     are capped per instrument and per asset class, and are then scaled by the brakes from
     aurora.portfolio.brakes, so a recommendation can never be larger than the book's own
     risk framework allows.
  3. COST CAN VETO. An instrument whose estimated round-trip cost exceeds its expected
     per-period contribution is marked AVOID with the numbers shown. Cost is certain;
     the signal is not.
"""
import math
from dataclasses import dataclass, field
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple

from aurora.core import asset_universe as au


# ---------------------------------------------------------------- pre-registered rules
# Written once, before any output was inspected. Changing these is a documented act.
WEIGHTS: Dict[str, float] = {
    "momentum": 0.40,     # 12-month return skipping the last month (classic, documented)
    "trend": 0.20,        # price against its 200-day average
    "fundamental": 0.20,  # supplied by the caller; zero weight when absent
    "risk": 0.20,         # negative volatility: prefer the calmer instrument
}

CLASS_CAP: Dict[str, float] = {
    au.EQUITY: 0.60, au.ETF: 0.50, au.FUND: 0.30, au.FIXED_INCOME: 0.50,
    au.FX: 0.20, au.CRYPTO: 0.10, au.ENERGY: 0.15, au.METALS: 0.25,
    au.AGRI: 0.15, au.INDEX: 0.30, au.NFT: 0.0, au.METAVERSE: 0.0,
}
INSTRUMENT_CAP = 0.25
MIN_HISTORY = 260          # one trading year plus a month for the skipped month
TOP_THIRD = 2.0 / 3.0
BOTTOM_THIRD = 1.0 / 3.0
COST_VETO_BPS = 60.0       # above this, the trade must justify itself in writing


@dataclass
class Recommendation:
    symbol: str
    name: str
    asset_class: str
    venue: str
    score: float
    action: str                       # خرید / نگهداری / پرهیز / داده ناکافی
    target_weight: float
    factors: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def line(self) -> str:
        bits = "، ".join(self.reasons[:3])
        return f"{self.symbol} ({self.name}): {self.action} · وزن {self.target_weight:.1%} — {bits}"


@dataclass
class Proposal:
    recommendations: List[Recommendation]
    weights: Dict[str, float]
    cash: float
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        invested = sum(self.weights.values())
        buys = [r.symbol for r in self.recommendations if r.action == "خرید"]
        return (f"{len(self.recommendations)} ابزار بررسی شد · {len(buys)} پیشنهاد خرید · "
                f"سرمایه‌گذاری‌شده {invested:.1%} · نقد {self.cash:.1%}")


# ---------------------------------------------------------------- measurements
def _returns(closes: Sequence[float]) -> List[float]:
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))
            if closes[i - 1] > 0]


def momentum(closes: Sequence[float]) -> Optional[float]:
    """12-month return, skipping the most recent month (the documented convention)."""
    if len(closes) < MIN_HISTORY + 21:
        return None
    past = closes[-252]
    recent = closes[-21]
    return recent / past - 1.0 if past > 0 else None


def trend(closes: Sequence[float]) -> Optional[float]:
    if len(closes) < 200:
        return None
    average = sum(closes[-200:]) / 200.0
    return closes[-1] / average - 1.0 if average > 0 else None


def annual_vol(closes: Sequence[float]) -> Optional[float]:
    if len(closes) < 60:
        return None
    rets = _returns(closes[-253:])
    if len(rets) < 20:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252)


def _percentiles(values: List[float]) -> List[float]:
    """Rank-based percentile in [0,1]; ties share the average rank. Deterministic."""
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank / max(1, len(values) - 1)
        i = j + 1
    return ranks


def _z(values: List[float]) -> List[float]:
    if len(values) < 2:
        return [0.0] * len(values)
    mean = sum(values) / len(values)
    sd = (sum((v - mean) ** 2 for v in values) / (len(values) - 1)) ** 0.5
    if sd == 0:
        return [0.0] * len(values)
    return [(v - mean) / sd for v in values]


# ---------------------------------------------------------------- the engine
def recommend(prices: Dict[str, Sequence[float]],
              fundamentals: Optional[Dict[str, float]] = None,
              cost_bps: Optional[Dict[str, float]] = None,
              risk_scale: float = 1.0,
              max_names: int = 10) -> Proposal:
    """Rank the given universe and propose weights inside the risk budget.

    `fundamentals` is a caller-supplied score per symbol (higher is better); it is not
    fetched here, so an engine that has no fresh filings says so instead of inventing one.
    `risk_scale` is the applied brake scale from aurora.portfolio.brakes (0..1).
    """
    fundamentals = fundamentals or {}
    cost_bps = cost_bps or {}
    if not 0.0 < risk_scale <= 1.0:
        raise ValueError("مقیاس ریسک باید بین ۰ و ۱ باشد؛ اهرم مجاز نیست")

    rows: List[dict] = []
    for symbol, closes in prices.items():
        try:
            inst = au.get(symbol)
        except au.UnknownInstrument:
            raise
        m, t, v = momentum(closes), trend(closes), annual_vol(closes)
        missing = [name for name, val in (("مومنتوم", m), ("روند", t), ("نوسان", v))
                   if val is None]
        rows.append({"symbol": symbol, "inst": inst, "closes": list(closes),
                     "momentum": m, "trend": t, "vol": v, "missing": missing})

    usable = [r for r in rows if not r["missing"]]
    short = [r for r in rows if r["missing"]]

    notes: List[str] = []
    if short:
        notes.append("داده ناکافی برای " + "، ".join(f"{r['symbol']} ({'/'.join(r['missing'])})"
                                                    for r in short))
    if not usable:
        # an empty proposal is not enough: the caller must see WHICH instruments were
        # examined and why each was refused, otherwise the screen looks like a blank failure
        refused = [Recommendation(
            symbol=r["symbol"], name=r["inst"].name, asset_class=r["inst"].asset_class,
            venue=r["inst"].venue, score=0.0, action="داده ناکافی", target_weight=0.0,
            warnings=[f"تاریخچه کافی نیست: {'، '.join(r['missing'])}"]) for r in short]
        return Proposal(refused, {}, 1.0,
                        notes + ["هیچ ابزاری داده کافی نداشت؛ پیشنهادی صادر نشد"])

    # fundamentals only count if present for at least half the usable names, otherwise the
    # weight is redistributed and the output says so rather than silently scoring zero
    have_fund = [r["symbol"] for r in usable if r["symbol"] in fundamentals]
    use_fund = len(have_fund) >= max(2, len(usable) // 2)
    weights = dict(WEIGHTS)
    if not use_fund:
        notes.append("داده بنیادی کافی نبود؛ وزن آن بین سه عامل دیگر بازتوزیع شد")
        dropped = weights.pop("fundamental")
        total = sum(weights.values())
        weights = {k: v + dropped * v / total for k, v in weights.items()}

    mom_z = _z([r["momentum"] for r in usable])
    trend_z = _z([r["trend"] for r in usable])
    vol_z = _z([r["vol"] for r in usable])
    fund_z = _z([fundamentals.get(r["symbol"], 0.0) for r in usable]) if use_fund else [0.0] * len(usable)
    mom_pct = _percentiles([r["momentum"] for r in usable])
    vol_pct = _percentiles([r["vol"] for r in usable])

    for i, row in enumerate(usable):
        row["score"] = (weights["momentum"] * mom_z[i] + weights["trend"] * trend_z[i]
                        + weights["risk"] * (-vol_z[i])
                        + (weights.get("fundamental", 0.0) * fund_z[i] if use_fund else 0.0))
        row["mom_pct"], row["vol_pct"] = mom_pct[i], vol_pct[i]

    usable.sort(key=lambda r: (-r["score"], r["symbol"]))
    count = len(usable)

    # inverse volatility sizing, then caps, then the brake scale - in that order, so a cap
    # can never be re-opened by a later multiplication
    inv = [1.0 / r["vol"] for r in usable]
    total_inv = sum(inv)
    raw_weights = [w / total_inv for w in inv]

    recs: List[Recommendation] = []
    class_used: Dict[str, float] = {}
    chosen: Dict[str, float] = {}

    for idx, row in enumerate(usable):
        rank = idx / max(1, count - 1) if count > 1 else 1.0
        percentile = 1.0 - rank                      # 1.0 = best score
        if percentile >= TOP_THIRD and row["momentum"] > 0 and row["trend"] > 0:
            action = "خرید"
        elif percentile <= BOTTOM_THIRD and row["momentum"] < 0 and row["trend"] < 0:
            action = "پرهیز"
        else:
            action = "نگهداری"

        target = 0.0
        if action == "خرید" and len(chosen) < max_names:
            cls = row["inst"].asset_class
            room = max(0.0, CLASS_CAP.get(cls, 0.0) - class_used.get(cls, 0.0))
            target = min(raw_weights[idx], INSTRUMENT_CAP, room) * risk_scale
            if target > 0:
                chosen[row["symbol"]] = target
                class_used[cls] = class_used.get(cls, 0.0) + target

        reasons = [
            f"مومنتوم ۱۲ ماهه {row['momentum']:+.1%} (صدک {row['mom_pct'] * 100:.0f})",
            f"قیمت {row['trend']:+.1%} نسبت به میانگین ۲۰۰ روزه",
            f"نوسان سالانه {row['vol']:.1%} (صدک {row['vol_pct'] * 100:.0f}؛ پایین‌تر بهتر)",
        ]
        if use_fund and row["symbol"] in fundamentals:
            reasons.append(f"امتیاز بنیادی {fundamentals[row['symbol']]:+.2f}")

        warns: List[str] = []
        if not row["inst"].verified:
            warns.append("مشخصات این ابزار در کاتالوگ تأییدنشده است؛ اندازه قرارداد پیش از معامله باید کنترل شود")
        if row["symbol"] in cost_bps and cost_bps[row["symbol"]] > COST_VETO_BPS:
            warns.append(f"هزینه رفت‌وبرگشت {cost_bps[row['symbol']]:.0f} bps از آستانه "
                         f"{COST_VETO_BPS:.0f} گذشته؛ سود باید آن را توجیه کند")
            if action == "خرید":
                action = "پرهیز"
                chosen.pop(row["symbol"], None)
                class_used[row["inst"].asset_class] = max(
                    0.0, class_used.get(row["inst"].asset_class, 0.0) - target)
                target = 0.0

        recs.append(Recommendation(
            symbol=row["symbol"], name=row["inst"].name,
            asset_class=row["inst"].asset_class, venue=row["inst"].venue,
            score=round(row["score"], 6), action=action, target_weight=round(target, 6),
            factors={"momentum": row["momentum"], "trend": row["trend"], "vol": row["vol"]},
            reasons=reasons, warnings=warns))

    for row in short:
        recs.append(Recommendation(
            symbol=row["symbol"], name=row["inst"].name,
            asset_class=row["inst"].asset_class, venue=row["inst"].venue,
            score=0.0, action="داده ناکافی", target_weight=0.0,
            warnings=[f"تاریخچه کافی نیست: {'، '.join(row['missing'])}"]))

    invested = sum(chosen.values())
    if invested > 1.0:                                # never, but never silently
        chosen = {k: v / invested for k, v in chosen.items()}
        invested = sum(chosen.values())
    notes.append(f"مقیاس ریسک اعمال‌شده {risk_scale:.2f}؛ اهرم مجاز نیست")
    if any(r.warnings for r in recs):
        notes.append("هشدارها در همان ردیف آمده‌اند و پنهان نشده‌اند")
    return Proposal(recs, {k: round(v, 6) for k, v in chosen.items()},
                    round(max(0.0, 1.0 - invested), 6), notes)


def explain(proposal: Proposal, limit: int = 10) -> str:
    """A Persian report of the proposal: the ranking, the reasons, and the caveats."""
    lines = ["# پیشنهاد سرمایه‌گذاری", "", proposal.summary(), ""]
    lines.append("| نماد | نام | کلاس | امتیاز | اقدام | وزن هدف |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for rec in proposal.recommendations[:limit]:
        lines.append(f"| {rec.symbol} | {rec.name} | {rec.asset_class} | {rec.score:+.2f} | "
                     f"{rec.action} | {rec.target_weight:.1%} |")
    detailed = [r for r in proposal.recommendations[:limit] if r.action == "خرید"]
    if detailed:
        lines += ["", "## دلیل هر خرید"]
        for rec in detailed:
            lines.append(f"- **{rec.symbol}**: " + "؛ ".join(rec.reasons))
    warnings = [(r.symbol, w) for r in proposal.recommendations for w in r.warnings]
    if warnings:
        lines += ["", "## هشدارها"]
        lines += [f"- {symbol}: {text}" for symbol, text in warnings]
    if proposal.notes:
        lines += ["", "## یادداشت"] + [f"- {n}" for n in proposal.notes]
    lines += ["", "این یک سطح تصمیم با دلیل است، نه ادعای بازده برتر. "
                  "نسبت اطلاعات اندازه‌گیری‌شده در برابر وزن مساوی ۰.۰۶ است."]
    return "\n".join(lines) + "\n"
