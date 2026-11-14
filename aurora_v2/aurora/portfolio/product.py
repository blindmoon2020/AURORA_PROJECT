"""The product face: what AURORA can prove about itself, on one page.

Path 3 is not a better return. It is a claim that survives scrutiny: costs are measured,
risk is bounded and stress-tested, every decision is on a hash-chained ledger, and no
number is printed without the caveat that belongs to it.

This module is what makes that sellable rather than asserted. It puts three things side
by side for the first time - the pre-trade cost of what we are about to do, the loss the
combined book would take in a crisis, and how much of that is one bet rather than two.

The rule the whole report obeys: a number we cannot compute is reported as UNPRICED,
never as zero. "No cost measured" and "no cost" are different statements, and confusing
them is how a cost model quietly becomes a marketing document.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from aurora.execution.impact import estimate
from aurora.portfolio.risk_budget import (concentration_check, covariance_matrix,
                                          diversification_ratio, risk_contributions)
from aurora.portfolio.scenarios import margin_of_safety, replay_all
from aurora.portfolio.stress import (block_bootstrap, bootstrap, correlated_shock,
                                     liquidation_days)


@dataclass
class OrderScreen:
    symbol: str
    notional: float
    participation: Optional[float]
    total_bps: Optional[float]
    allowed: bool
    reason: str


@dataclass
class ProductReport:
    orders: List[OrderScreen] = field(default_factory=list)
    sleeve_dd_median: Optional[float] = None
    sleeve_dd_p95: Optional[float] = None
    sleeve_breach: Optional[float] = None
    crisis_loss_pct: Optional[float] = None
    diversification: Optional[float] = None
    concentration_ok: Optional[bool] = None
    concentration_worst: Optional[float] = None
    risk_shares: Dict[str, float] = field(default_factory=dict)
    liquidation_days: Dict[str, float] = field(default_factory=dict)
    scenarios: List[tuple] = field(default_factory=list)
    shock_to_breach_pct: Optional[float] = None
    limit_pct: float = 40.0
    unpriced: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def refused(self) -> List[OrderScreen]:
        return [o for o in self.orders if not o.allowed]


def adv_notional(candles: Sequence, window: int = 20) -> Optional[float]:
    """Average daily traded value. None when volume is absent, not zero."""
    if not candles:
        return None
    tail = [c for c in candles[-window:] if getattr(c, "volume", None)]
    if not tail:
        return None
    values = [c.close * c.volume for c in tail]
    avg = sum(values) / len(values)
    return avg if avg > 0 else None


def daily_vol_bps(closes: Sequence[float], window: int = 60) -> Optional[float]:
    if len(closes) < window + 1:
        return None
    tail = closes[-window - 1:]
    rets = [tail[i] / tail[i - 1] - 1.0 for i in range(1, len(tail)) if tail[i - 1] > 0]
    if len(rets) < 20:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return (var ** 0.5) * 10000.0


def screen_orders(weights: Dict[str, float], prices: Dict[str, float], equity: float,
                  candles: Dict[str, Sequence], cap: float = 0.10) -> List[OrderScreen]:
    """Price every order before it becomes a ticket, and refuse what must not be sent."""
    out: List[OrderScreen] = []
    for sym, w in sorted(weights.items()):
        price = prices.get(sym)
        if not price:
            out.append(OrderScreen(sym, 0.0, None, None, False,
                                   "refused: no price, so no notional and no cost"))
            continue
        notional = abs(w) * equity
        adv = adv_notional(candles.get(sym, []))
        vol = daily_vol_bps([c.close for c in candles.get(sym, [])]) or 100.0
        if adv is None:
            out.append(OrderScreen(sym, notional, None, None, True,
                                   "UNPRICED: volume unavailable, cost not measured"))
            continue
        est = estimate(notional, adv, vol, cap=cap)
        out.append(OrderScreen(sym, notional, est.participation, est.total_bps,
                               est.allowed, est.reason or "within the participation cap"))
    return out


def build_report(equity_weights: Dict[str, float], sleeve_weights: Dict[str, float],
                 orders: Sequence[OrderScreen], sleeve_returns: Sequence[float],
                 equity_returns: Sequence[float],
                 prices: Dict[str, float], equity: float,
                 candles: Dict[str, Sequence],
                 dd_limit_pct: float = 40.0) -> ProductReport:
    rep = ProductReport(orders=list(orders), limit_pct=dd_limit_pct)
    rep.unpriced = [o.symbol for o in orders if o.total_bps is None]

    if sleeve_returns:
        res = bootstrap(sleeve_returns, paths=300, limit_pct=dd_limit_pct,
                        label="sleeve iid")
        rep.sleeve_dd_median = res.worst_dd_pct
        rep.sleeve_dd_p95 = res.p95_dd_pct
        rep.sleeve_breach = res.breach_rate
        blocks = block_bootstrap(sleeve_returns, paths=150, block=6, limit_pct=dd_limit_pct)
        rep.notes.append(f"بوت‌استرپ بلوکی: میانه افت {blocks.worst_dd_pct:.1f}% "
                         f"(p95 {blocks.p95_dd_pct:.1f}%)")

    combined = dict(equity_weights)
    for sym, w in sleeve_weights.items():
        combined[sym] = combined.get(sym, 0.0) + w
    shocks = {s: -0.20 for s in combined}
    rep.crisis_loss_pct = correlated_shock(combined, shocks, crisis_correlation=1.0) * 100

    series = {}
    if equity_returns:
        series["equity"] = list(equity_returns)
    if sleeve_returns:
        series["cross"] = list(sleeve_returns)
    if len(series) == 2:
        cov = covariance_matrix(series)
        w = {"equity": sum(equity_weights.values()), "cross": sum(sleeve_weights.values())}
        total = sum(w.values()) or 1.0
        w = {k: v / total for k, v in w.items()}
        rep.diversification = diversification_ratio(w, cov)
        ok, worst, shares = concentration_check(w, cov, limit=0.75)
        rep.concentration_ok, rep.concentration_worst = ok, worst
        rep.risk_shares = shares

    try:
        rep.scenarios = [(r.name, r.loss_pct, r.breaches_limit)
                         for r in replay_all(combined, limit_pct=dd_limit_pct)]
        rep.shock_to_breach_pct = margin_of_safety(combined, dd_limit_pct)["shock_to_breach_pct"]
    except Exception:
        rep.notes.append("بازپخش سناریوهای تاریخی محاسبه نشد")

    if rep.diversification is None:
        rep.notes.append("همبستگی و سهم ریسک سلیوها پس از بیست جلسه بازده ثبت‌شده محاسبه می‌شود")

    for sym, w in combined.items():
        adv = adv_notional(candles.get(sym, []))
        price = prices.get(sym)
        if adv and price:
            rep.liquidation_days[sym] = liquidation_days(abs(w) * equity, adv)
        elif w:
            rep.liquidation_days[sym] = float("inf")
    return rep


def markdown(rep: ProductReport, calibration_note: str = "") -> str:
    lines = ["# گزارش محصول AURORA", "",
             "این صفحه فقط چیزهایی را می‌گوید که قابل اثبات است. هر عددی که محاسبه نشده، "
             "«قیمت‌گذاری‌نشده» نوشته می‌شود، نه صفر.",
             "", "مبالغ بر پایه سرمایه گزارشی ۱۰۰٬۰۰۰ واحد است؛ دفتر پیپر واحدسازمانی "
             "است و سرمایه واقعی ندارد.", ""]
    lines += ["## هزینه پیش از سفارش", "",
              "| نماد | مبلغ | سهم از حجم روز | هزینه | وضعیت |",
              "| --- | --- | --- | --- | --- |"]
    for o in rep.orders:
        part = f"{o.participation:.3%}" if o.participation is not None else "—"
        cost = f"{o.total_bps:.1f} bps" if o.total_bps is not None else "UNPRICED"
        state = "تأیید" if o.allowed else "**رد**"
        lines.append(f"| {o.symbol} | {o.notional:,.0f} | {part} | {cost} | {state} |")
    if rep.unpriced:
        lines += ["", f"بدون قیمت‌گذاری (حجم نامعلوم): {', '.join(rep.unpriced)}"]
    if rep.refused:
        lines += ["", "**سفارش‌های رد شده:**"] + [f"- {o.symbol}: {o.reason}" for o in rep.refused]

    lines += ["", "## ریسک سبد", ""]
    if rep.sleeve_dd_p95 is not None:
        lines.append(f"- افت بدترین حالت سلیو (بوت‌استرپ): میانه {rep.sleeve_dd_median:.1f}% · "
                     f"p95 {rep.sleeve_dd_p95:.1f}% · نرخ نقض {rep.sleeve_breach:.1%}")
    if rep.crisis_loss_pct is not None:
        lines.append(f"- شوک بحران با همبستگی کامل: {rep.crisis_loss_pct:.1f}%")
    if rep.diversification is not None:
        lines.append(f"- نسبت تنوع (۱ = بدون تنوع): {rep.diversification:.2f}")
    if rep.concentration_ok is not None:
        verdict = "قبول" if rep.concentration_ok else "**هشدار: یک سلیو بیشتر ریسک را دارد**"
        lines.append(f"- تمرکز ریسک: بیشترین سهم {rep.concentration_worst:.0%} — {verdict}")
    if rep.scenarios:
        lines += ["", "## سناریوهای تاریخی روی همین سبد", "",
                  "| بحران | اثر | حد |", "| --- | --- | --- |"]
        for name, loss, breach in rep.scenarios:
            lines.append(f"| {name} | {loss:+.1f}% | {'**نقض**' if breach else 'داخل حد'} |")
        if rep.shock_to_breach_pct is not None:
            lines.append("")
            lines.append(f"شوک یکنواختی که حد {rep.limit_pct:.0f}٪ را می‌شکند: "
                         f"**{rep.shock_to_breach_pct:.1f}%** افت همزمان.")
    hard = {k: v for k, v in rep.liquidation_days.items() if v != float("inf")}
    if hard:
        worst = sorted(hard.items(), key=lambda kv: kv[1], reverse=True)[:3]
        lines.append("- کندترین خروج‌ها: " + "، ".join(
            f"{s} " + ("<0.1 روز" if d < 0.1 else f"{d:.1f} روز") for s, d in worst))
    if rep.notes:
        lines += [""] + [f"- {n}" for n in rep.notes]
    if calibration_note:
        lines += ["", f"**کالیبراسیون هزینه:** {calibration_note}"]
    lines += ["", "## آنچه این گزارش نمی‌گوید", "",
              "- هیچ ادعای بازدهی برتری ندارد؛ بازده اثبات‌شده در برابر سبد هم‌وزن وجود ندارد.",
              "- پر شدن واقعی و لغزش واقعی تا اولین اجرا اندازه‌گیری نشده است."]
    return "\n".join(lines)
