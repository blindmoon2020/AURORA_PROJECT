"""Portfolio-wide risk: real correlation and historical VaR, not a docstring promise.

Provenance: this module came from the donor repo (aurora-quant-platform) where the file claimed
"correlation risk" in its docstring while computing only unrealised PnL and a position count.
Ported under MIT, then rewritten: the claims and the arithmetic now agree, and the old monitor
API is preserved so nothing that imported it breaks.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class OpenPosition:
    symbol: str
    size: float
    entry_price: float
    current_price: float
    is_buy: bool = True


# ---------------------------------------------------------------- correlation / VaR
def _aligned(returns_by_symbol: Dict[str, Sequence[float]]) -> Tuple[List[str], List[List[float]]]:
    """Keep only series long enough to say anything, and trim them to a common length."""
    usable = {s: list(r) for s, r in returns_by_symbol.items() if len(r) >= 2}
    if not usable:
        return [], []
    n = min(len(r) for r in usable.values())
    names = sorted(usable)
    return names, [usable[s][-n:] for s in names]


def correlation_matrix(returns_by_symbol: Dict[str, Sequence[float]]) -> Dict[str, Dict[str, float]]:
    """Pearson correlation on aligned series; identical series give exactly 1.0."""
    names, cols = _aligned(returns_by_symbol)
    out: Dict[str, Dict[str, float]] = {}
    for i, a in enumerate(names):
        out[a] = {}
        for j, b in enumerate(names):
            if i == j:
                out[a][b] = 1.0
                continue
            va, vb = cols[i], cols[j]
            ma, mb = sum(va) / len(va), sum(vb) / len(vb)
            cov = sum((x - ma) * (y - mb) for x, y in zip(va, vb))
            sa = math.sqrt(sum((x - ma) ** 2 for x in va))
            sb = math.sqrt(sum((y - mb) ** 2 for y in vb))
            if sa == 0 or sb == 0:
                out[a][b] = 0.0
            else:
                # clamp: floating point must not report 0.9999999999999999 for identical series
                value = cov / (sa * sb)
                if value >= 1.0 - 1e-12:
                    value = 1.0
                elif value <= -1.0 + 1e-12:
                    value = -1.0
                elif abs(value) < 1e-12:
                    value = 0.0
                out[a][b] = value
    return out


def portfolio_returns(returns_by_symbol: Dict[str, Sequence[float]],
                      weights: Dict[str, float]) -> List[float]:
    """Weighted portfolio return series, restricted to the symbols present in both inputs."""
    names = [s for s in weights if s in returns_by_symbol and len(returns_by_symbol[s]) >= 2]
    if not names:
        raise ValueError("هیچ نمادی میان وزن‌ها و سری بازده مشترک نیست")
    cols = _aligned({s: returns_by_symbol[s] for s in names})[1]
    w = [weights[s] for s in names]
    return [sum(wi * ci[k] for wi, ci in zip(w, cols)) for k in range(len(cols[0]))]


def historical_var(returns_by_symbol: Dict[str, Sequence[float]], weights: Dict[str, float],
                   confidence: float = 0.95) -> float:
    """Historical VaR as a positive loss fraction; no normal assumption.

    95% VaR answers: in the worst 5% of observed days, the loss is at least this large.
    """
    if not 0.5 <= confidence < 1.0:
        raise ValueError("سطح اطمینان باید میان ۰.۵ و ۱ باشد")
    series = sorted(portfolio_returns(returns_by_symbol, weights))
    idx = int(math.floor((1.0 - confidence) * (len(series) - 1)))
    return max(0.0, -series[idx])


def diversification_ratio(returns_by_symbol: Dict[str, Sequence[float]],
                          weights: Dict[str, float]) -> float:
    """1.0 means no diversification benefit; below 1.0 means the weights offset each other."""
    names = [s for s in weights if s in returns_by_symbol and len(returns_by_symbol[s]) >= 2]
    if not names:
        raise ValueError("برای محاسبه نسبت تنوع، بازده مشترک لازم است")
    indiv = []
    for s in names:
        r = returns_by_symbol[s]
        mu = sum(r) / len(r)
        sd = math.sqrt(sum((x - mu) ** 2 for x in r) / max(1, len(r) - 1))
        indiv.append(weights[s] * sd)
    port = portfolio_returns(returns_by_symbol, weights)
    mu = sum(port) / len(port)
    sd_p = math.sqrt(sum((x - mu) ** 2 for x in port) / max(1, len(port) - 1))
    return 1.0 if sd_p == 0 else sum(indiv) / sd_p


# ---------------------------------------------------------------- the pre-trade monitor
@dataclass(frozen=True)
class PortfolioVerdict:
    approved: bool
    reason: str
    var_pct: Optional[float] = None
    drawdown_pct: float = 0.0
    diversification: Optional[float] = None


class PortfolioRiskMonitor:
    """Aggregate exposure, drawdown and (when returns are supplied) portfolio VaR."""

    def __init__(self, max_total_drawdown_pct: float = 0.05, max_open_positions: int = 5,
                 max_var_pct: float = 0.03, confidence: float = 0.95) -> None:
        if not 0 < max_total_drawdown_pct <= 1:
            raise ValueError("سقف افت باید کسری میان ۰ و ۱ باشد")
        self.max_dd_pct = max_total_drawdown_pct
        self.max_positions = max_open_positions
        self.max_var_pct = max_var_pct
        self.confidence = confidence

    def unrealized_drawdown_pct(self, positions: Iterable[OpenPosition], capital: float) -> float:
        pnl = 0.0
        for p in positions:
            diff = (p.current_price - p.entry_price) if p.is_buy else (p.entry_price - p.current_price)
            pnl += diff * p.size
        return 0.0 if capital <= 0 else abs(min(0.0, pnl)) / capital

    def evaluate_portfolio_risk(self, positions: List[OpenPosition], current_capital: float,
                                returns_by_symbol: Optional[Dict[str, Sequence[float]]] = None,
                                weights: Optional[Dict[str, float]] = None) -> PortfolioVerdict:
        """Every check names itself in the reason, so a refusal is never a mystery."""
        if len(positions) >= self.max_positions:
            return PortfolioVerdict(False, f"سقف پوزیشن همزمان پر است ({self.max_positions})")

        dd = self.unrealized_drawdown_pct(positions, current_capital)
        if dd >= self.max_dd_pct:
            return PortfolioVerdict(False, f"افت سبد از سقف گذشت ({dd:.2%})", drawdown_pct=dd)

        var = div = None
        if returns_by_symbol and weights:
            var = historical_var(returns_by_symbol, weights, self.confidence)
            div = diversification_ratio(returns_by_symbol, weights)
            if var > self.max_var_pct:
                return PortfolioVerdict(
                    False, f"VaR {self.confidence:.0%} برابر {var:.2%} و بالای سقف {self.max_var_pct:.2%}",
                    var_pct=var, drawdown_pct=dd, diversification=div)

        if div is not None and div > 0.98 and len(positions) > 1:
            return PortfolioVerdict(
                False, "تنوع واقعی وجود ندارد: ریسک سبد تقریباً جمع ریسک تک‌تک اجزاست",
                var_pct=var, drawdown_pct=dd, diversification=div)

        reason = "همه بررسی‌های ریسک سبد گذشت"
        if var is not None:
            reason += f" · VaR {var:.2%} · نسبت تنوع {div:.2f}"
        return PortfolioVerdict(True, reason, var_pct=var, drawdown_pct=dd, diversification=div)
