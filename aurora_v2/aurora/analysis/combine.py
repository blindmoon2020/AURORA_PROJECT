"""Choose which analysis to trust for THIS instrument, then combine technical and fundamental.

The owner's point is the design principle: gold may obey smart-money structure while ignoring a
trendline; wheat may obey a breakout while its "fundamentals" are an inventory report. A platform
that applies one method everywhere is not powerful, it is brittle. So selection is explicit:

  weight(method) = class bias × regime multiplier × measured fitness (shrunk toward the prior)

Nothing here invents fitness. Without measurement the prior stands, and the report says so.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from aurora.analysis import advanced_ta as ta
from aurora.analysis import trend_rules as tr
from aurora.analysis.fundamental import macro_score, score_company
from aurora.analysis.technical import EVALUATORS, METHOD_CLASS_BIAS, Verdict, evaluate_all, slope_pct

TRENDING, RANGING = "روندی", "رنج"

# how much of the score each source carries, by asset class; frozen before measurement
BLEND: Dict[str, Tuple[float, float, float]] = {
    "equity": (0.50, 0.30, 0.20),
    "etf": (0.50, 0.25, 0.25),
    "index": (0.55, 0.15, 0.30),
    "metals": (0.55, 0.15, 0.30),
    "energy": (0.55, 0.10, 0.35),
    "agri": (0.55, 0.10, 0.35),
    "fx": (0.45, 0.00, 0.55),
    "crypto": (0.55, 0.05, 0.40),
    "fixed_income": (0.40, 0.10, 0.50),
    "fund": (0.55, 0.30, 0.15),
}
SHRINK_K = 20.0          # observations needed before measured fitness outweighs the prior
CONFLICT = 0.15


@dataclass
class CombinedView:
    symbol: str
    asset_class: str
    regime: str
    verdict: str
    score: float
    confidence: float
    size_multiplier: float
    technical: List[Verdict] = field(default_factory=list)
    fundamental: Optional[object] = None
    macro: Optional[object] = None
    chosen: List[Tuple[str, float, str]] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def regime_of(bars: Sequence) -> str:
    """Trend when the 50-EMA slope is large relative to daily range, else range."""
    closes = [b.close for b in bars]
    if len(closes) < 60:
        return RANGING
    e = tr.ema_series(closes, 50)
    slope = slope_pct(e, 20) or 0.0
    atr = ta.atr_pct([b.high for b in bars], [b.low for b in bars], closes, 14) or 1.0
    return TRENDING if abs(slope) > 0.5 * atr else RANGING


def select(asset_class: str, regime: str,
           fitness: Optional[Dict[str, Tuple[float, int]]] = None) -> List[Tuple[str, float, str]]:
    """Rank methods for this class and regime, with the reason each weight came out as it did."""
    bias = METHOD_CLASS_BIAS.get(asset_class) or METHOD_CLASS_BIAS["equity"]
    out: List[Tuple[str, float, str]] = []
    for name, fn in EVALUATORS.items():
        family = {"structure": "structure", "trend": "trend", "momentum": "momentum",
                  "breakout": "breakout", "mean_reversion": "mean_reversion", "flow": "flow"}[name]
        w = bias.get(family, 0.5)
        mult, why = 1.0, ""
        if regime == TRENDING and family in ("trend", "momentum", "structure"):
            mult, why = 1.2, "بازار روندی"
        elif regime == RANGING and family == "mean_reversion":
            mult, why = 1.3, "بازار رنج"
        elif regime == RANGING and family in ("trend", "momentum"):
            mult, why = 0.8, "روند در بازار رنج کم‌اثر است"
        w *= mult
        if fitness and name in fitness:
            value, n = fitness[name]
            w = (w * SHRINK_K + max(0.0, value) * n) / (SHRINK_K + n)
            why = (why + " · " if why else "") + f"کارایی اندازه‌گیری‌شده روی {n} نمونه"
        out.append((name, round(w, 3), why or "وزن پیش‌فرض کلاس"))
    return sorted(out, key=lambda r: r[1], reverse=True)


def combine(symbol: str, asset_class: str, bars: Sequence,
            metrics: Optional[Dict[str, float]] = None,
            drivers: Optional[Dict[str, float]] = None,
            fitness: Optional[Dict[str, Tuple[float, int]]] = None) -> CombinedView:
    regime = regime_of(bars)
    chosen = select(asset_class, regime, fitness)
    weights = {name: w for name, w, _ in chosen}
    verdicts = evaluate_all(bars, asset_class)
    tech_score, wsum = 0.0, 0.0
    reasons = []
    for v in verdicts:
        w = weights.get(v.method, 0.5) * v.confidence
        tech_score += v.score * w
        wsum += w
        reasons.append(f"{v.method}: {v.score:+.2f} (وزن {w:.2f})")
    tech = tech_score / wsum if wsum else 0.0

    fund = score_company(metrics) if metrics else None
    macro = macro_score(asset_class, drivers) if drivers else None

    wt, wf, wm = BLEND.get(asset_class, BLEND["equity"])
    parts, total_w = [(tech, wt)], wt
    if fund is not None and fund.confidence > 0:
        parts.append((fund.score, wf * min(1.0, fund.confidence + 0.5)))
        total_w += wf * min(1.0, fund.confidence + 0.5)
    if macro is not None and macro.confidence > 0:
        parts.append((macro.score, wm * min(1.0, macro.confidence + 0.5)))
        total_w += wm * min(1.0, macro.confidence + 0.5)
    score = sum(s * w for s, w in parts) / total_w if total_w else 0.0

    conflicts = []
    if fund is not None and fund.confidence > 0 and tech * fund.score < 0 \
            and min(abs(tech), abs(fund.score)) > CONFLICT:
        conflicts.append(f"تضاد تکنیکال ({tech:+.2f}) و بنیادی ({fund.score:+.2f})")
    if macro is not None and macro.confidence > 0 and tech * macro.score < 0 \
            and min(abs(tech), abs(macro.score)) > CONFLICT:
        conflicts.append(f"تضاد تکنیکال ({tech:+.2f}) و ماکرو ({macro.score:+.2f})")

    label = "خرید" if score > 0.2 else "فروش" if score < -0.2 else "خنثی"
    if conflicts:
        label = "تضاد · بدون معامله" if abs(score) < 0.35 else label + " (اندازه نصف)"
    confidence = min(1.0, abs(score) * 1.4)
    size = 0.5 if conflicts else 1.0

    notes = []
    if not metrics:
        notes.append("داده بنیادی نبود: وزن آن صفر شد و بین بقیه بازتوزیع شد")
    if not drivers:
        notes.append("راننده ماکرو نبود: سهم ماکرو حذف شد")
    if not fitness:
        notes.append("کارایی روش‌ها هنوز اندازه‌گیری نشده: وزن‌ها پیش‌فرض کلاس‌اند")
    return CombinedView(symbol, asset_class, regime, label, round(score, 4), round(confidence, 3),
                        size, verdicts, fund, macro, chosen, conflicts, notes)


def explain(view: CombinedView) -> str:
    lines = [f"# تحلیل ترکیبی {view.symbol}", "",
             f"- کلاس: {view.asset_class} · رژیم: {view.regime}",
             f"- نتیجه: **{view.verdict}** · امتیاز {view.score:+.3f} · اطمینان {view.confidence:.0%}",
             f"- ضریب اندازه پوزیشن: {view.size_multiplier:.1f}", "",
             "## انتخاب روش‌ها", "", "| روش | وزن | دلیل |", "| --- | --- | --- |"]
    lines += [f"| {n} | {w:.2f} | {why or '—'} |" for n, w, why in view.chosen]
    lines += ["", "## تکنیکال", ""]
    lines += [f"- **{v.method}** {v.score:+.2f} · " + "؛ ".join(v.reasons) for v in view.technical] or ["- داده کافی نبود"]
    if view.fundamental is not None:
        lines += ["", "## بنیادی", "", f"امتیاز {view.fundamental.score:+.2f} (اطمینان {view.fundamental.confidence:.0%})"]
        lines += [f"- {r}" for r in view.fundamental.reasons]
        lines += [f"- ⚠️ {w}" for w in view.fundamental.warnings]
    if view.macro is not None:
        lines += ["", "## ماکرو", "", f"امتیاز {view.macro.score:+.2f}"]
        lines += [f"- {r}" for r in view.macro.reasons]
    if view.conflicts:
        lines += ["", "## تضادها", ""] + [f"- {c}" for c in view.conflicts]
    if view.notes:
        lines += ["", "## آنچه این تحلیل نمی‌گوید", ""] + [f"- {n}" for n in view.notes]
    return "\n".join(lines) + "\n"
