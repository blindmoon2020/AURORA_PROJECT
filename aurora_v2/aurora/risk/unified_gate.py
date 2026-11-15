"""Unified Enterprise Risk Gate: combines single-trade Prop rules,
correlated portfolio risk (sqrt(r' C r)), volatility scaling, and news lockouts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from ..core.types import Side
from ..portfolio.allocation import PortfolioDecision, PortfolioRisk
from .engine import RiskDecision, RiskEngine


@dataclass(frozen=True)
class GateEvaluation:
    approved: bool
    symbol: str
    side: str
    final_units: float
    effective_risk_money: float
    portfolio_risk_after_pct: float
    class_risk_after_pct: float
    volatility_scalar: float
    reason: str
    ts: int

    def to_audit_dict(self) -> Dict[str, Any]:
        """Structured payload for API dashboards and compliance logs."""
        return asdict(self)


class UnifiedRiskGate:
    """Single entry point before any order reaches an execution bridge."""

    def __init__(self, engine: RiskEngine, portfolio: PortfolioRisk) -> None:
        self.engine = engine
        self.portfolio = portfolio
        self.news_lockout_reason: Optional[str] = None

    def set_news_lockout(self, reason: Optional[str]) -> None:
        """Pause new entries during high-impact macroeconomic events."""
        self.news_lockout_reason = reason

    def evaluate_order(
        self,
        *,
        symbol: str,
        asset_class: str,
        side: Side,
        entry: float,
        stop: float,
        equity: float,
        volatility_scalar: float = 1.0,
        ts: int = 0,
    ) -> GateEvaluation:
        """
        Runs full institutional pre-trade checks:
        1. High-impact news blackout check
        2. Single-trade RiskEngine checks (kill-switch, daily cap, geometry, leverage)
        3. Volatility-adjusted sizing (scales units down in turbulent regimes)
        4. Correlated PortfolioRisk check (sqrt(r' C r) & asset-class caps)
        """
        if self.news_lockout_reason:
            return GateEvaluation(
                approved=False,
                symbol=symbol,
                side=side.value,
                final_units=0.0,
                effective_risk_money=0.0,
                portfolio_risk_after_pct=0.0,
                class_risk_after_pct=0.0,
                volatility_scalar=volatility_scalar,
                reason=f"news lockout active: {self.news_lockout_reason}",
                ts=ts,
            )

        if not 0.1 <= volatility_scalar <= 1.5:
            return GateEvaluation(
                approved=False,
                symbol=symbol,
                side=side.value,
                final_units=0.0,
                effective_risk_money=0.0,
                portfolio_risk_after_pct=0.0,
                class_risk_after_pct=0.0,
                volatility_scalar=volatility_scalar,
                reason=f"invalid volatility_scalar {volatility_scalar} (must be in [0.1, 1.5])",
                ts=ts,
            )

        # Step 1: Account & Single-Trade Risk Check
        trade_dec: RiskDecision = self.engine.evaluate(
            symbol=symbol,
            side=side,
            entry=entry,
            stop=stop,
            equity=equity,
            ts=ts,
        )
        if not trade_dec.approved:
            return GateEvaluation(
                approved=False,
                symbol=symbol,
                side=side.value,
                final_units=0.0,
                effective_risk_money=0.0,
                portfolio_risk_after_pct=0.0,
                class_risk_after_pct=0.0,
                volatility_scalar=volatility_scalar,
                reason=trade_dec.reason,
                ts=ts,
            )

        # Step 2: Apply Volatility Scaling
        scaled_units = round(trade_dec.units * volatility_scalar, 6)
        scaled_risk_money = round(trade_dec.risk_money * volatility_scalar, 2)
        if scaled_units <= 0:
            return GateEvaluation(
                approved=False,
                symbol=symbol,
                side=side.value,
                final_units=0.0,
                effective_risk_money=0.0,
                portfolio_risk_after_pct=0.0,
                class_risk_after_pct=0.0,
                volatility_scalar=volatility_scalar,
                reason="units reduced to zero after volatility scaling",
                ts=ts,
            )

        # Step 3: Portfolio Correlation & Asset Class Concentration Check
        port_dec: PortfolioDecision = self.portfolio.evaluate(
            symbol=symbol,
            asset_class=asset_class,
            risk_money=scaled_risk_money,
            equity=equity,
        )
        if not port_dec.approved:
            return GateEvaluation(
                approved=False,
                symbol=symbol,
                side=side.value,
                final_units=0.0,
                effective_risk_money=scaled_risk_money,
                portfolio_risk_after_pct=port_dec.risk_after_pct,
                class_risk_after_pct=port_dec.class_risk_after_pct,
                volatility_scalar=volatility_scalar,
                reason=port_dec.reason,
                ts=ts,
            )

        return GateEvaluation(
            approved=True,
            symbol=symbol,
            side=side.value,
            final_units=scaled_units,
            effective_risk_money=scaled_risk_money,
            portfolio_risk_after_pct=port_dec.risk_after_pct,
            class_risk_after_pct=port_dec.class_risk_after_pct,
            volatility_scalar=volatility_scalar,
            reason=f"APPROVED | {trade_dec.reason} | {port_dec.reason} | vol_scalar={volatility_scalar}x",
            ts=ts,
        )

    def commit_fill(self, symbol: str, asset_class: str, notional: float, risk_money: float) -> None:
        """Synchronizes both RiskEngine and PortfolioRisk upon order execution."""
        self.engine.register_open(symbol, notional)
        self.portfolio.add(symbol, asset_class, risk_money)

    def commit_close(self, symbol: str, pnl: float) -> None:
        """Synchronizes both RiskEngine and PortfolioRisk upon position exit."""
        self.engine.register_close(symbol, pnl)
        self.portfolio.remove(symbol)