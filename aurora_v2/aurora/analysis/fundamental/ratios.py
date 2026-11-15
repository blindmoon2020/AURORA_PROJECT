"""The fundamental package: valuation, quality, growth and the macro drivers per asset class.

Two honest limits are stated here rather than discovered later by a user:

1. Sector neutrality is not implemented. A P/E of 12 is cheap for software and expensive for a
   bank, so the scores here are absolute-threshold opinions, flagged as such in every reason.
2. Fundamentals are quarterly. They cannot produce a trade signal on their own; they set the
   side and the size, while technical analysis sets the timing. That division is enforced in
   `aurora.analysis.combine`, not left to the reader's good sense.

Macro drivers are a small, explicit table instead of a regression, because a fitted macro model
on the free data available here would be an overfit dressed as research. Each entry states a
sign, and the sign is a testable claim, not a coefficient.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

GOOD, WEAK = 1.0, -1.0


@dataclass(frozen=True)
class FundamentalScore:
    score: float                                   # -1..+1
    confidence: float                              # 0..1, share of inputs actually present
    components: Dict[str, float] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _pe(v: Optional[float]) -> Optional[float]:
    if v is None or v <= 0:
        return None                                # a negative P/E is a loss, not a bargain
    return GOOD if v < 15 else (0.0 if v < 25 else WEAK)


def _pb(v: Optional[float]) -> Optional[float]:
    if v is None or v <= 0:
        return None
    return GOOD if v < 1.5 else (0.0 if v < 3.0 else WEAK)


def _roe(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return GOOD if v > 0.15 else (0.0 if v > 0.08 else WEAK)


def _margin(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return GOOD if v > 0.12 else (0.0 if v > 0.05 else WEAK)


def _debt(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return GOOD if v < 0.8 else (0.0 if v < 1.8 else WEAK)


def _growth(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    return GOOD if v > 0.10 else (0.0 if v > 0.0 else WEAK)


CHECKS = (
    ("pe", _pe, "P/E"),
    ("pb", _pb, "P/B"),
    ("roe", _roe, "ROE"),
    ("margin", _margin, "حاشیه سود"),
    ("debt_to_equity", _debt, "بدهی به حقوق صاحبان"),
    ("revenue_growth", _growth, "رشد درآمد"),
)


def score_company(metrics: Dict[str, Optional[float]]) -> FundamentalScore:
    """Absolute-threshold score over whatever metrics exist. Absent metrics carry no vote."""
    values: Dict[str, float] = {}
    reasons: List[str] = []
    for key, fn, label in CHECKS:
        raw = metrics.get(key)
        try:
            verdict = fn(raw)
        except (TypeError, ValueError):
            verdict = None
        if verdict is None:
            continue
        values[key] = verdict
        if verdict > 0:
            reasons.append(f"{label} مطلوب ({raw})")
        elif verdict < 0:
            reasons.append(f"{label} ضعیف ({raw})")
    if not values:
        return FundamentalScore(0.0, 0.0, {}, [], ["هیچ نسبت بنیادی موجود نیست"])
    score = sum(values.values()) / len(CHECKS)
    conf = len(values) / len(CHECKS)
    warns = []
    if conf < 1.0:
        warns.append(f"فقط {len(values)} از {len(CHECKS)} نسبت موجود است")
    warns.append("نسبت‌ها مطلق‌اند نه صنعت‌محور: مقایسه فقط درون همان صنعت معتبر است")
    return FundamentalScore(max(-1.0, min(1.0, score)), conf, values, reasons, warns)


# ------------------------------------------------------------------ macro drivers
# +1 means "this driver rising supports the asset", -1 means it works against it.
MACRO_SIGNS: Dict[str, Dict[str, float]] = {
    "equity": {"real_yield": -0.6, "dollar": -0.2, "pmi": +0.5, "credit_spread": -0.5},
    "etf": {"real_yield": -0.5, "dollar": -0.2, "pmi": +0.4, "credit_spread": -0.4},
    "index": {"real_yield": -0.6, "dollar": -0.2, "pmi": +0.5, "credit_spread": -0.5},
    "metals": {"real_yield": -0.8, "dollar": -0.5, "pmi": +0.1, "credit_spread": -0.2},
    "energy": {"dollar": -0.3, "pmi": +0.6, "real_yield": 0.1, "credit_spread": -0.2},
    "agri": {"dollar": -0.4, "pmi": +0.3, "real_yield": 0.0, "credit_spread": -0.1},
    "fx": {"real_yield": -0.3, "dollar": -0.4, "pmi": +0.2, "credit_spread": -0.2},
    "crypto": {"real_yield": -0.5, "dollar": -0.3, "pmi": +0.1, "credit_spread": -0.3},
    "fixed_income": {"real_yield": -0.8, "pmi": +0.3, "credit_spread": -0.4, "dollar": 0.1},
    "fund": {"real_yield": -0.5, "pmi": +0.4, "credit_spread": -0.4, "dollar": -0.2},
}


def macro_score(asset_class: str, drivers: Dict[str, float]) -> FundamentalScore:
    """Combine signed macro drivers. Values are the driver's own change, standardised elsewhere."""
    signs = MACRO_SIGNS.get(asset_class)
    if not signs:
        return FundamentalScore(0.0, 0.0, {}, [], [f"راننده ماکرو برای کلاس {asset_class} تعریف نشده"])
    used, total = {}, 0.0
    reasons: List[str] = []
    for name, sign in signs.items():
        value = drivers.get(name)
        if value is None:
            continue
        contribution = sign * value
        total += contribution
        used[name] = round(contribution, 3)
        reasons.append(f"{name} {'حامی' if contribution > 0 else 'مخالف'} ({value:+.2f} × {sign:+.1f})")
    weight_sum = sum(abs(signs[k]) for k in used) or 1.0
    return FundamentalScore(max(-1.0, min(1.0, total / weight_sum)),
                            len(used) / len(signs), used, reasons,
                            [] if used else ["هیچ راننده ماکرو موجود نیست"])
