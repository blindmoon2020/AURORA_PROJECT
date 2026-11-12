"""Portfolio risk: two correlated positions are not two independent risks.

The single-symbol engine sizes one trade. This module answers the question a
desk actually asks: after this new position, what is the risk of the book?
It uses the standard parametric aggregation, sqrt(r' C r), on money-at-risk
vectors, with a correlation estimate built from returns or from a fallback rule.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class PortfolioLimits:
    max_portfolio_risk_pct: float = 1.5      # of equity, aggregated
    max_class_risk_pct: float = 1.0          # per asset class
    max_positions: int = 6
    same_class_correlation: float = 0.6      # fallback when no history
    cross_class_correlation: float = 0.2


@dataclass(frozen=True)
class PortfolioDecision:
    approved: bool
    reason: str
    risk_after_pct: float
    class_risk_after_pct: float
    effective_risk_money: float


@dataclass
class Position:
    symbol: str
    asset_class: str
    risk_money: float


def correlation(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    """Pearson correlation of two return series; None when undefined."""
    n = min(len(a), len(b))
    if n < 3:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((x - mb) ** 2 for x in b)
    if va <= 0 or vb <= 0:
        return None
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    rho = cov / math.sqrt(va * vb)
    return max(-1.0, min(1.0, rho))


@dataclass
class CorrelationMatrix:
    values: Dict[Tuple[str, str], float] = field(default_factory=dict)
    same_class: float = 0.6
    cross_class: float = 0.2
    class_of: Callable[[str], str] = lambda s: "unknown"

    @classmethod
    def from_returns(cls, returns: Dict[str, Sequence[float]],
                     same_class: float = 0.6, cross_class: float = 0.2,
                     class_of: Callable[[str], str] = lambda s: "unknown") -> "CorrelationMatrix":
        values: Dict[Tuple[str, str], float] = {}
        symbols = list(returns)
        for i, a in enumerate(symbols):
            for b in symbols[i + 1:]:
                rho = correlation(returns[a], returns[b])
                if rho is not None:
                    values[(a, b)] = values[(b, a)] = rho
        return cls(values=values, same_class=same_class, cross_class=cross_class, class_of=class_of)

    def get(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        if (a, b) in self.values:
            return self.values[(a, b)]
        if (b, a) in self.values:          # a matrix is symmetric; a dict may not be
            return self.values[(b, a)]
        return self.same_class if self.class_of(a) == self.class_of(b) else self.cross_class


class PortfolioRisk:
    def __init__(self, limits: PortfolioLimits, corr: CorrelationMatrix):
        self.limits = limits
        self.corr = corr
        self.positions: List[Position] = []

    def effective_risk(self, positions: Iterable[Position]) -> float:
        ps = list(positions)
        total = 0.0
        for i, p in enumerate(ps):
            for j, q in enumerate(ps):
                total += p.risk_money * q.risk_money * self.corr.get(p.symbol, q.symbol)
        return math.sqrt(max(total, 0.0))

    def current_risk_money(self) -> float:
        return self.effective_risk(self.positions)

    def class_risk_money(self, asset_class: str) -> float:
        subset = [p for p in self.positions if p.asset_class == asset_class]
        return self.effective_risk(subset)

    def evaluate(self, symbol: str, asset_class: str, risk_money: float,
                 equity: float) -> PortfolioDecision:
        if len(self.positions) >= self.limits.max_positions:
            return PortfolioDecision(False, f"portfolio: max positions {self.limits.max_positions} reached",
                                     0.0, 0.0, self.current_risk_money())
        if any(p.symbol == symbol for p in self.positions):
            return PortfolioDecision(False, f"portfolio: already holding {symbol}", 0.0, 0.0,
                                     self.current_risk_money())
        candidate = Position(symbol, asset_class, risk_money)
        book = self.positions + [candidate]
        risk_after = self.effective_risk(book)
        class_after = self.effective_risk([p for p in book if p.asset_class == asset_class])
        risk_pct = risk_after / equity * 100.0 if equity else 0.0
        class_pct = class_after / equity * 100.0 if equity else 0.0
        if risk_pct > self.limits.max_portfolio_risk_pct:
            return PortfolioDecision(False,
                                     f"portfolio: book risk would be {risk_pct:.2f}% > "
                                     f"{self.limits.max_portfolio_risk_pct:.2f}%",
                                     risk_pct, class_pct, risk_after)
        if class_pct > self.limits.max_class_risk_pct:
            return PortfolioDecision(False,
                                     f"portfolio: {asset_class} risk would be {class_pct:.2f}% > "
                                     f"{self.limits.max_class_risk_pct:.2f}%",
                                     risk_pct, class_pct, risk_after)
        return PortfolioDecision(True,
                                 f"portfolio: book risk {risk_pct:.2f}% of equity "
                                 f"({len(book)} positions, corr-adjusted)",
                                 risk_pct, class_pct, risk_after)

    def add(self, symbol: str, asset_class: str, risk_money: float) -> None:
        self.positions.append(Position(symbol, asset_class, risk_money))

    def remove(self, symbol: str) -> None:
        self.positions = [p for p in self.positions if p.symbol != symbol]
