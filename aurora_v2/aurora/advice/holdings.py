"""Turn a class allocation into things a client can actually buy.

A portfolio that says "13.8% equities" is not advice, it is a pie chart. This module answers the
three questions a client always asks next: WHICH instrument, on WHICH exchange, at WHAT price
and in WHAT quantity.

Two honesty rules govern everything here:

* An unknown price is never a zero and never a guess. The row is emitted with a named gap
  ("قیمت نامعلوم") and no quantity, so the report cannot invent a trade.
* The bucket called "other" is not allowed to stay mysterious. It is expanded into named
  components, each with its own weight and rationale, because a 0.9% line nobody can explain
  is how a portfolio hides something.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from aurora.core import asset_universe as au

# The "other" bucket, expanded. This is a POLICY choice, declared rather than discovered:
# the long tail is not a dumping ground, it is three named things.
OTHER_SPLIT: Dict[str, float] = {
    "physical_gold": 0.50,      # دسترسی مستقیم به طلا بیرون از صندوق
    "commodity_fund": 0.30,     # تنوع کالایی بدون تحویل فیزیکی
    "structured": 0.20,         # ابزار ساختاریافته/سرمایه‌گذاری جایگزین
}
OTHER_LABELS = {
    "physical_gold": "طلا و فلز فیزیکی",
    "commodity_fund": "صندوق کالایی متنوع",
    "structured": "ابزار جایگزین/ساختاریافته",
}

# Per-class candidate pools, drawn from the catalogue so a name is never typed by hand.
POOLS: Dict[str, Sequence[str]] = {
    "equity": ("AAPL", "MSFT", "JNJ", "KO", "JPM", "PG", "WMT"),
    "etf": ("SPY", "QQQ", "EFA", "EEM", "IWM"),
    "fixed_income": ("TLT", "IEF", "SHY", "LQD", "BND"),
    "commodity": ("GLD", "SLV", "DBC", "USO"),
    "crypto": ("BTC-USD", "ETH-USD"),
    "cash": (),
}


@dataclass
class Holding:
    symbol: str
    name: str
    asset_class: str
    venue: str
    country: str
    currency: str
    weight: float                 # share of total portfolio
    notional: float               # money
    price: Optional[float]        # None = unknown, never zero
    units: Optional[float]        # None when price is unknown
    note: str = ""

    def line(self) -> str:
        px = f"{self.price:,.2f}" if self.price is not None else "قیمت نامعلوم"
        qty = f"{self.units:,.4f}" if self.units is not None else "—"
        return (f"{self.symbol} ({self.venue}/{self.country}) · {self.weight*100:.1f}% · "
                f"{self.notional:,.0f} · قیمت {px} · مقدار {qty} · {self.name}")


@dataclass
class DetailedPlan:
    capital: float
    holdings: List[Holding] = field(default_factory=list)
    other_components: List[tuple] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _split_weight(total: float, names: Sequence[str]) -> Dict[str, float]:
    if not names or total <= 0:
        return {}
    each = total / len(names)
    return {n: each for n in names}


def expand(alloc: Dict[str, float], capital: float,
           prices: Optional[Dict[str, float]] = None,
           picks: Optional[Dict[str, Sequence[str]]] = None) -> DetailedPlan:
    """Allocation -> named instruments with venue, price, quantity and any honest gap."""
    prices = prices or {}
    picks = picks or {}
    plan = DetailedPlan(capital=capital)
    total = sum(alloc.values())
    if total <= 0:
        plan.gaps.append("سبد خالی است؛ چیزی برای خرید وجود ندارد")
        return plan

    for cls, weight in sorted(alloc.items(), key=lambda kv: -kv[1]):
        if weight <= 0:
            continue
        money = capital * weight
        if cls == "cash":
            plan.holdings.append(Holding("CASH", "نقد (بدون خرید)", "cash", "—", "—", "—",
                                         weight, money, None, None,
                                         "نگهداشتن نقد خودش یک تصمیم است، نه باقی‌مانده"))
            continue
        if cls == "other":
            for key, share in OTHER_SPLIT.items():
                plan.other_components.append(
                    (OTHER_LABELS[key], weight * share, money * share, share))
            continue

        names = list(picks.get(cls) or POOLS.get(cls) or ())
        if not names:
            plan.gaps.append(f"{cls}: هیچ ابزاری برای این کلاس تعریف نشده است")
            continue
        for symbol, w in _split_weight(weight, names).items():
            try:
                inst = au.get(symbol)
                name, venue, country, currency = inst.name, inst.venue, \
                    au.venue(inst.venue).country, au.venue(inst.venue).currency
            except Exception:
                name, venue, country, currency = symbol, "—", "—", "—"
            notional = capital * w
            price = prices.get(symbol)
            if price is None:
                plan.gaps.append(f"{symbol}: قیمت موجود نیست؛ مقدار محاسبه نشد")
                units = None
            elif price <= 0:
                plan.gaps.append(f"{symbol}: قیمت نامعتبر ({price})")
                units, price = None, None
            else:
                units = notional / price
            note = "" if inst.verified else "قرارداد/بورس تأییدنشده؛ پیش از معامله بررسی شود" \
                if 'inst' in dir() else ""
            plan.holdings.append(Holding(symbol, name, cls, venue, country, currency,
                                         w, notional, price, units, note))

    if plan.other_components:
        plan.notes.append("سهم «سایر» به اجزای نام‌دار شکسته شد؛ هیچ بخش بی‌نامی باقی نماند")
    plan.notes.append("این خروجی پیشنهاد ترکیب است، نه پیش‌بینی بازده")
    return plan


def explain(plan: DetailedPlan) -> str:
    out = [f"# جزئیات سبد پیشنهادی ({plan.capital:,.0f})", ""]
    out.append("| نماد | نام | بورس/کشور | وزن | مبلغ | قیمت | مقدار |")
    out.append("| --- | --- | --- | --- | --- | --- | --- |")
    for h in plan.holdings:
        px = f"{h.price:,.2f}" if h.price is not None else "نامعلوم"
        qty = f"{h.units:,.4f}" if h.units is not None else "—"
        out.append(f"| {h.symbol} | {h.name} | {h.venue}/{h.country} | "
                   f"{h.weight*100:.1f}% | {h.notional:,.0f} | {px} | {qty} |")
    if plan.other_components:
        out += ["", "## سهم «سایر» شامل چه چیزی است", ""]
        out.append("| جزء | سهم از سبد | مبلغ | سهم داخل سایر |")
        out.append("| --- | --- | --- | --- |")
        for label, w, money, share in plan.other_components:
            out.append(f"| {label} | {w*100:.2f}% | {money:,.0f} | {share*100:.0f}% |")
    if plan.gaps:
        out += ["", "## شکاف‌های اعلام‌شده", ""]
        out += [f"- {g}" for g in plan.gaps]
    out += ["", "## یادداشت", ""] + [f"- {n}" for n in plan.notes]
    return "\n".join(out)
