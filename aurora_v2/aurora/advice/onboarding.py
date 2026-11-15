"""Client onboarding: risk questionnaire -> profile -> portfolio -> rebalance advice.

What this module is for
-----------------------
The platform must take a customer's details and liquidity, run a risk/psychology
questionnaire, and then keep designing and updating a portfolio for them while the
subscription is paid. That is a suitability engine, so the rules have to be explicit and
testable, not a paragraph of marketing.

Three deliberate constraints
----------------------------
1. A questionnaire answers TWO different questions that are often confused: what the client
   CAN afford to lose (capacity: age, horizon, emergency fund, income stability) and what the
   client CAN SLEEP WITH (tolerance: stated reaction to a drawdown, experience). The binding
   number is the LOWER of the two: a young investor who panics still gets the cautious
   allocation, because the panic is what actually gets realised.
2. No return is ever promised or projected here. The output is an exposure and a set of
   trades, plus the reason for each.
3. Advice is gated on the subscription. When it lapses the engine stops issuing changes; it
   does not silently keep the portfolio drifting.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# ------------------------------------------------------------------ questionnaire
# Each question carries options with a score 0..4 (higher = more risk capacity/tolerance).
QUESTIONS: Tuple[dict, ...] = (
    {"id": "horizon", "kind": "capacity", "text": "این پول چند سال می‌تواند سرمایه‌گذاری بماند؟",
     "options": [("کمتر از ۱ سال", 0), ("۱ تا ۳ سال", 1), ("۳ تا ۵ سال", 2),
                 ("۵ تا ۱۰ سال", 3), ("بیش از ۱۰ سال", 4)]},
    {"id": "emergency", "kind": "capacity", "text": "پشتوانه نقدی اضطراری چند ماه زندگی شماست؟",
     "options": [("ندارم", 0), ("کمتر از ۳ ماه", 1), ("۳ تا ۶ ماه", 2),
                 ("۶ تا ۱۲ ماه", 3), ("بیش از ۱۲ ماه", 4)]},
    {"id": "income", "kind": "capacity", "text": "ثبات درآمد شما چگونه است؟",
     "options": [("بی‌ثبات", 0), ("نسبتاً بی‌ثبات", 1), ("متوسط", 2),
                 ("پایدار", 3), ("بسیار پایدار", 4)]},
    {"id": "share", "kind": "capacity", "text": "این مبلغ چه سهمی از کل دارایی شماست؟",
     "options": [("بیش از ۷۵٪", 0), ("۵۰ تا ۷۵٪", 1), ("۲۵ تا ۵۰٪", 2),
                 ("۱۰ تا ۲۵٪", 3), ("کمتر از ۱۰٪", 4)]},
    {"id": "drawdown", "kind": "tolerance", "text": "اگر سبد شما در یک ماه ۲۰٪ افت کند چه می‌کنید؟",
     "options": [("همه را می‌فروشم", 0), ("بخشی را می‌فروشم", 1), (" کاری نمی‌کنم", 2),
                 ("کمی اضافه می‌کنم", 3), ("به‌طور جدی اضافه می‌کنم", 4)]},
    {"id": "experience", "kind": "tolerance", "text": "تجربه شما با ابزارهای پرنوسان؟",
     "options": [("هیچ", 0), ("کمی (سپرده و صندوق)", 1), ("سهام", 2),
                 ("اهرم و آتی", 3), ("حرفه‌ای", 4)]},
    {"id": "goal", "kind": "tolerance", "text": "هدف اصلی شما از این سرمایه‌گذاری؟",
     "options": [("حفظ سرمایه", 0), ("درآمد پایدار", 1), ("رشد متعادل", 2),
                 ("رشد بلندمدت", 3), ("رشد حداکثری", 4)]},
)

BANDS: Tuple[Tuple[str, float, float], ...] = (
    ("محافظه‌کار", 0.0, 20.0),
    ("محافظه‌کار متعادل", 20.0, 40.0),
    ("متعادل", 40.0, 60.0),
    ("رشدگرا", 60.0, 80.0),
    ("تهاجمی", 80.0, 100.1),
)

# band -> maximum share of the portfolio allowed in risk assets, and the drawdown the
# design must survive. The drawdown column is what makes the profile actionable.
BAND_LIMITS: Dict[str, dict] = {
    "محافظه‌کار":        {"risk_assets": 0.20, "max_dd": 8.0},
    "محافظه‌کار متعادل": {"risk_assets": 0.40, "max_dd": 15.0},
    "متعادل":           {"risk_assets": 0.60, "max_dd": 22.0},
    "رشدگرا":           {"risk_assets": 0.80, "max_dd": 30.0},
    "تهاجمی":           {"risk_assets": 0.95, "max_dd": 40.0},
}


@dataclass(frozen=True)
class Profile:
    score: float
    band: str
    capacity_score: float
    tolerance_score: float
    binding: str                     # "ظرفیت" or "تحمل" - which one limited the client
    risk_asset_cap: float
    max_drawdown_pct: float
    reasons: Tuple[str, ...] = ()

    def line(self) -> str:
        return (f"{self.band} · امتیاز {fa_digits(f'{self.score:.0f}')}/۱۰۰ · سقف دارایی پرریسک "
                f"{self.risk_asset_cap:.0%} · افت قابل‌تحمل {self.max_drawdown_pct:.0f}% "
                f"(محدودکننده: {self.binding})")


def _band_for(score: float) -> str:
    for name, low, high in BANDS:
        if low <= score < high:
            return name
    return BANDS[-1][0]


def score_answers(answers: Dict[str, int]) -> Profile:
    """answers maps question id -> index of the chosen option."""
    if not answers:
        raise ValueError("پرسشنامه خالی است؛ بدون پاسخ نمی‌توان پروفایل ساخت")
    capacity, tolerance, reasons = [], [], []
    for q in QUESTIONS:
        if q["id"] not in answers:
            reasons.append(f"پرسش «{q['id']}» بی‌پاسخ ماند و در امتیاز لحاظ نشد")
            continue
        idx = answers[q["id"]]
        if not isinstance(idx, int) or idx < 0 or idx >= len(q["options"]):
            raise ValueError(f"پاسخ نامعتبر برای {q['id']}: {idx!r}")
        value = q["options"][idx][1]
        (capacity if q["kind"] == "capacity" else tolerance).append(value)

    if not capacity or not tolerance:
        raise ValueError("برای ساخت پروفایل به هر دو بخش ظرفیت و تحمل پاسخ لازم است")

    cap_pct = sum(capacity) / (4.0 * len(capacity)) * 100.0
    tol_pct = sum(tolerance) / (4.0 * len(tolerance)) * 100.0
    # the binding constraint is the lower of the two, then a small penalty for disagreement
    low, binding = (cap_pct, "ظرفیت") if cap_pct <= tol_pct else (tol_pct, "تحمل")
    gap = abs(cap_pct - tol_pct)
    score = max(0.0, low - 0.25 * gap)
    if gap >= 25:
        reasons.append(f"اختلاف زیاد میان ظرفیت ({cap_pct:.0f}) و تحمل ({tol_pct:.0f}): "
                       "سبد محتاطانه‌تر بسته شد")
    band = _band_for(score)
    limits = BAND_LIMITS[band]
    return Profile(score=round(score, 1), band=band, capacity_score=round(cap_pct, 1),
                   tolerance_score=round(tol_pct, 1), binding=binding,
                   risk_asset_cap=limits["risk_assets"], max_drawdown_pct=limits["max_dd"],
                   reasons=tuple(reasons))


# ------------------------------------------------------------------ portfolio design
# The core sleeve is a fixed, boring block; the rest is what the profile is allowed to add.
CORE_TEMPLATE: Tuple[Tuple[str, float], ...] = (
    ("cash", 0.10),
    ("fixed_income", 0.25),
    ("equity", 0.45),
    ("commodity", 0.12),
    ("crypto", 0.05),
    ("other", 0.03),
)

CLASS_LABELS = {"cash": "نقد", "fixed_income": "اوراق و درآمد ثابت", "equity": "سهام",
                "commodity": "کالا و طلا", "crypto": "رمزارز", "other": "سایر"}


def fa_digits(text: str) -> str:
    """Persian digits for anything a client reads; code and storage stay Latin."""
    table = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(text).translate(table)


def design_portfolio(profile: Profile, risk_scale: float = 1.0) -> Dict[str, float]:
    """Turn a profile into class weights that respect its cap, then scale for the market brake."""
    if not 0.0 <= risk_scale <= 1.0:
        raise ValueError("ضریب ریسک باید بین ۰ و ۱ باشد؛ بالای ۱ یعنی اهرم و مجاز نیست")
    risky = {"equity", "commodity", "crypto", "other"}
    base = dict(CORE_TEMPLATE)
    risky_weight = sum(base[k] for k in risky)
    cap = max(0.0, min(profile.risk_asset_cap * risk_scale, 1.0))
    target_risky = min(risky_weight, cap)
    if target_risky <= 0:
        return {"cash": 1.0}
    factor = target_risky / risky_weight
    for k in risky:
        base[k] *= factor
    freed = risky_weight - target_risky
    base["cash"] += freed * 0.30
    base["fixed_income"] += freed * 0.70
    total = sum(base.values())
    return {k: v / total for k, v in base.items() if v > 0}



# ------------------------------------------------------------------ rebalancing
@dataclass(frozen=True)
class Trade:
    asset_class: str
    side: str            # "افزودن" / "کاهش"
    delta_pct: float     # share of portfolio, signed in absolute terms
    amount: float        # currency units
    reason: str

    def line(self) -> str:
        return (f"{self.side} {CLASS_LABELS.get(self.asset_class, self.asset_class)} "
                f"{fa_digits(f'{abs(self.delta_pct):.1%}')} "
                f"({fa_digits(f'{abs(self.amount):,.0f}')}) · {self.reason}")


def rebalance(current: Dict[str, float], target: Dict[str, float], capital: float,
              band: float = 0.02, min_amount: float = 50.0,
              cost_bps: float = 10.0) -> List[Trade]:
    """What to add, what to cut, and by how much - with a dead band so it is not churn."""
    if capital <= 0:
        raise ValueError("سرمایه باید مثبت باشد")
    if band < 0:
        raise ValueError("باند باید نامنفی باشد")
    trades: List[Trade] = []
    for cls in sorted(set(current) | set(target)):
        cur = float(current.get(cls, 0.0))
        tgt = float(target.get(cls, 0.0))
        delta = tgt - cur
        if abs(delta) < band:
            continue                                   # inside the band: leave it alone
        amount = delta * capital
        if abs(amount) < min_amount:
            continue
        cost = abs(amount) * cost_bps / 10_000.0
        if cost > abs(amount) * 0.02:
            continue                                   # a trade that costs 2% of itself is not worth it
        trades.append(Trade(asset_class=cls, side="افزودن" if delta > 0 else "کاهش",
                            delta_pct=round(delta, 6), amount=round(amount, 2),
                            reason=(f"هدف {tgt:.0%} در برابر فعلی {cur:.0%}؛ "
                                    f"فاصله بیرون باند {band:.0%}")))
    trades.sort(key=lambda t: -abs(t.delta_pct))
    return trades


# ------------------------------------------------------------------ subscription gate
@dataclass(frozen=True)
class Access:
    allowed: bool
    reason: str
    stale_days: Optional[int] = None


def subscription_gate(paid_until_iso: Optional[str], today_iso: str,
                      grace_days: int = 3) -> Access:
    """Analysis and rebalancing continue only while the subscription is paid."""
    if not paid_until_iso:
        return Access(False, "اشتراک ثبت نشده؛ تحلیل و به‌روزرسانی سبد صادر نمی‌شود")
    from datetime import date
    try:
        paid = date.fromisoformat(paid_until_iso)
        today = date.fromisoformat(today_iso)
    except ValueError as exc:
        raise ValueError(f"تاریخ نامعتبر: {exc}") from exc
    gap = (today - paid).days
    if gap > grace_days:
        return Access(False, f"اشتراک {gap} روز پیش پایان یافته؛ تا تمدید، سبد منجمد است",
                      stale_days=gap)
    if gap > 0:
        return Access(True, f"در دوره تنفس {gap} روزه تمدید", stale_days=gap)
    return Access(True, f"اشتراک فعال تا {paid_until_iso}")


DISCLAIMER = ("این خروجی یک پیشنهاد مبتنی بر قواعد و مناسب‌سنجی است، نه وعده بازده. "
              "هیچ عدد بازدهی در این ماژول پیش‌بینی نمی‌شود؛ تصمیم نهایی با مشتری است.")


def onboarding_report(profile: Profile, allocation: Dict[str, float], capital: float,
                      trades: Sequence[Trade], access: Access) -> str:
    lines = ["# پروفایل و سبد پیشنهادی مشتری", "",
             f"- پروفایل: {profile.line()}",
             f"- سرمایه: {fa_digits(f'{capital:,.0f}')}",
             f"- دسترسی: {access.reason}", "",
             "## ترکیب پیشنهادی", ""]
    for cls, w in sorted(allocation.items(), key=lambda kv: -kv[1]):
        lines.append(f"- {CLASS_LABELS.get(cls, cls)}: {fa_digits(f'{w:.1%}')} "
                     f"({fa_digits(f'{w * capital:,.0f}')})")
    if trades:
        lines += ["", "## تغییرات لازم نسبت به سبد فعلی", ""]
        lines += [f"- {t.line()}" for t in trades]
    else:
        lines += ["", "سبد فعلی داخل باند است؛ تغییری لازم نیست (کنترل هزینه)"]
    lines += ["", "---", DISCLAIMER]
    return "\n".join(lines)


CONTRADICTION_RULES = (
    ("tolerance_exceeds_capacity",
     "تحمل ریسک اعلام‌شده از ظرفیت مالی بیشتر است: پاسخ‌ها هیجانی‌اند نه محاسبه‌شده"),
    ("short_horizon_aggressive",
     "افق کوتاه با پروفایل تهاجمی جمع نمی‌شود؛ ریسک در زمان کوتاه فرصت بازگشت ندارد"),
    ("no_buffer_high_risk",
     "بدون ذخیره اضطراری، ریسک بالا یعنی فروش اجباری در بدترین قیمت"),
    ("loss_claim_above_cap",
     "افت اعلام‌شده قابل تحمل، از سقف محاسبه‌شده پروفایل بیشتر است"),
)


def contradictions(answers: Dict[int, int], capacity: Dict[str, object],
                   profile: Optional[Profile] = None) -> List[str]:
    """Flags where a client's stated appetite and stated situation disagree.

    This is the one idea worth taking from the external project: a questionnaire can be
    answered consistently in total and still be internally inconsistent. Taking the lower of
    the two is the only safe resolution, and the client is told why.
    """
    prof = profile or score_answers(answers)
    flags: List[str] = []
    horizon = int(capacity.get("horizon_years", 0) or 0)
    buffer_months = float(capacity.get("emergency_fund_months", 0) or 0)
    claimed_loss = float(capacity.get("loss_tolerance_pct", 0) or 0)
    capacity_score = prof.capacity_score
    tolerance_score = prof.tolerance_score

    if tolerance_score - capacity_score >= 20:
        flags.append(CONTRADICTION_RULES[0][1])
    if horizon and horizon < 3 and prof.band in ("تهاجمی", "رشدگرا"):
        flags.append(CONTRADICTION_RULES[1][1])
    if buffer_months < 3 and prof.band in ("تهاجمی", "رشدگرا"):
        flags.append(CONTRADICTION_RULES[2][1])
    if claimed_loss > prof.max_drawdown_pct + 1e-9:
        flags.append(CONTRADICTION_RULES[3][1])
    return flags
